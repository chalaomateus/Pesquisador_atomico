import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minions_extract import build_extraction_prompt, run_extraction, cross_reference, dispatch

FAKE_PROVIDERS = [
    {"name": "gemini", "base_url": "https://fake/gemini", "model": "m1", "api_key": "k1"},
    {"name": "groq", "base_url": "https://fake/groq", "model": "m2", "api_key": "k2"},
]


def make_http_post(responses):
    """responses: dict base_url -> content string OR Exception instance."""
    def _post(url, headers, body):
        resp = responses[url]
        if isinstance(resp, Exception):
            raise resp
        return {"choices": [{"message": {"content": resp}}]}
    return _post


class TestBuildExtractionPrompt(unittest.TestCase):
    def test_includes_question_and_material(self):
        prompt = build_extraction_prompt("pergunta X", "material Y")
        self.assertIn("pergunta X", prompt)
        self.assertIn("material Y", prompt)
        self.assertIn("SOMENTE", prompt)


class TestRunExtraction(unittest.TestCase):
    def test_one_minion_succeeds(self):
        http_post = make_http_post({
            "https://fake/gemini": "[ALTA] a empresa foi fundada em 2020",
        })
        extractions, failures = run_extraction(
            "quando foi fundada?", "texto: a empresa foi fundada em 2020.",
            [FAKE_PROVIDERS[0]], http_post,
        )
        self.assertEqual(len(extractions), 1)
        self.assertEqual(extractions[0]["provider"], "gemini")
        self.assertEqual(failures, [])

    def test_one_minion_fails_does_not_block_the_others(self):
        http_post = make_http_post({
            "https://fake/gemini": RuntimeError("timeout"),
            "https://fake/groq": "[ALTA] a empresa foi fundada em 2020",
        })
        extractions, failures = run_extraction(
            "quando foi fundada?", "texto: a empresa foi fundada em 2020.",
            FAKE_PROVIDERS, http_post,
        )
        self.assertEqual(len(extractions), 1)
        self.assertEqual(extractions[0]["provider"], "groq")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["provider"], "gemini")


class TestCrossReference(unittest.TestCase):
    def test_claim_confirmed_by_two_minions_is_verificado(self):
        material = "a empresa foi fundada em 2020 em sao paulo."
        extractions = [
            {"provider": "gemini", "extraction": "a empresa foi fundada em 2020"},
            {"provider": "groq", "extraction": "a empresa foi fundada em 2020"},
        ]
        result = cross_reference(extractions, material)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "VERIFICADO")
        self.assertEqual(result[0]["confirmations"], 2)

    def test_claim_from_single_minion_is_nao_verificado_but_still_shown(self):
        material = "a empresa foi fundada em 2020 em sao paulo."
        extractions = [
            {"provider": "gemini", "extraction": "a empresa foi fundada em 2020"},
        ]
        result = cross_reference(extractions, material)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "NAO-VERIFICADO")
        self.assertEqual(result[0]["confirmations"], 1)
        self.assertEqual(result[0]["claim"], "a empresa foi fundada em 2020")

    def test_claim_not_traceable_to_material_is_nao_verificado_even_with_two_confirmations(self):
        material = "a empresa foi fundada em 2020 em sao paulo."
        extractions = [
            {"provider": "gemini", "extraction": "a empresa tem 500 funcionarios"},
            {"provider": "groq", "extraction": "a empresa tem 500 funcionarios"},
        ]
        result = cross_reference(extractions, material)
        self.assertEqual(result[0]["status"], "NAO-VERIFICADO")

    def test_zero_extractions_returns_empty_list(self):
        result = cross_reference([], "qualquer material")
        self.assertEqual(result, [])

    def test_short_quote_is_prefix_of_long_quote_from_different_provider(self):
        """Caso mínimo do bug real: gemini cita só a data, groq cita a
        frase inteira — a citação curta é substring da longa, devem
        convergir num único claim VERIFICADO mesmo comparando a LINHA
        inteira (que é diferente) e não só a citação."""
        material = "a instituicao foi fundada em 1985, como entidade sem fins lucrativos."
        extractions = [
            {"provider": "gemini", "extraction": '[ALTA] fundada em 1985. Trecho exato: "a instituicao foi fundada em 1985"'},
            {"provider": "groq", "extraction": '[ALTA] fundada em 1985. (Trecho: "a instituicao foi fundada em 1985, como entidade sem fins lucrativos.")'},
        ]
        result = cross_reference(extractions, material)
        verificados = [r for r in result if r["status"] == "VERIFICADO"]
        self.assertEqual(len(verificados), 1)
        self.assertEqual(verificados[0]["confirmations"], 2)
        self.assertEqual(sorted(verificados[0]["sources"]), ["gemini", "groq"])
        # claim é a citação mais longa/informativa do grupo, não a linha crua
        self.assertEqual(
            verificados[0]["claim"],
            "a instituicao foi fundada em 1985, como entidade sem fins lucrativos.",
        )

    def test_line_without_any_quote_falls_back_to_whole_line_exact_match(self):
        """Requisito 6: linha sem nenhuma citação entre aspas cai no
        comportamento antigo (linha inteira como chave, comparação exata)
        — não pode ser descartada."""
        material = "a empresa tem 500 funcionarios."
        extractions = [
            {"provider": "gemini", "extraction": "o material nao responde essa pergunta diretamente"},
        ]
        result = cross_reference(extractions, material)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "NAO-VERIFICADO")
        self.assertEqual(result[0]["claim"], "o material nao responde essa pergunta diretamente")

    def test_short_isolated_quote_does_not_bridge_two_distinct_long_claims(self):
        """Caso adversarial 1 (achado do revisor): uma citação curta
        isolada ("1969") é substring de DUAS citações longas que
        descrevem fatos DIFERENTES (fundação vs. endereço da sede) — sem
        a salvaguarda de comprimento mínimo, as 3 se fundem num grupo só
        e reportam "confirmado por 3 provedores" quando na verdade são 2
        fatos distintos, cada um confirmado por apenas 1 provedor."""
        material = "A empresa foi fundada em 1969 no Brasil. A sede fica na Rua 1969, no bairro Central."
        extractions = [
            {"provider": "gemini", "extraction": '[ALTA] Trecho exato: "A empresa foi fundada em 1969 no Brasil"'},
            {"provider": "cohere", "extraction": '[ALTA] trecho: "1969"'},
            {"provider": "groq", "extraction": '[ALTA] Trecho: "A sede fica na Rua 1969, no bairro Central"'},
        ]
        result = cross_reference(extractions, material)
        # Nenhum claim pode reunir os 3 provedores — são 2 fatos distintos
        for r in result:
            self.assertLess(
                r["confirmations"], 3,
                f"citação curta '1969' fundiu incorretamente fatos distintos: {r}",
            )
        # E nenhum vira VERIFICADO (cada fato tem só 1 provedor de verdade)
        self.assertFalse(any(r["status"] == "VERIFICADO" for r in result))

    def test_fabricated_long_quote_sharing_short_prefix_is_not_verificado(self):
        """Caso adversarial 2 (achado do revisor, o mais grave): um
        provedor cita um trecho real curto ("o gato correu"), outro
        "estende" com conteúdo fabricado que não está no material ("o
        gato correu voando pelo ceu ateh a lua"). Sem as salvaguardas,
        os dois convergem (o real é substring do fabricado) e o texto
        alucinado sai como VERIFICADO com 2 confirmações — o oposto do
        propósito do sistema (impedir que alucinação passe por
        verificada)."""
        material = "O gato correu pela rua."
        extractions = [
            {"provider": "a_real", "extraction": '[ALTA] trecho: "o gato correu"'},
            {"provider": "b_fabricado", "extraction": '[ALTA] trecho: "o gato correu voando pelo ceu ateh a lua"'},
        ]
        result = cross_reference(extractions, material)
        fabricado_norm = "o gato correu voando pelo ceu ateh a lua"
        for r in result:
            if fabricado_norm in r["claim"].lower():
                self.assertNotEqual(
                    r["status"], "VERIFICADO",
                    f"conteúdo fabricado saiu VERIFICADO: {r}",
                )
        self.assertFalse(any(r["status"] == "VERIFICADO" for r in result))

    def test_five_real_provider_formatting_styles_converge_via_quote_matching(self):
        """Regressão baseada nos 5 formatos REAIS observados na
        verificação ao vivo da Embraer (Task 4), genericizados para um
        fato de teste. Antes da correção, as 5 linhas — todas com
        formatação diferente (aspas retas vs curvas, ordem do marcador,
        markdown do Mistral) — batiam 1 confirmação cada e ficavam todas
        NAO-VERIFICADO mesmo concordando no fato. Depois da correção, a
        citação entre aspas de cada linha converge num único grupo."""
        material = (
            "A instituicao foi fundada em 15 de marco de 1985, como uma "
            "entidade sem fins lucrativos vinculada ao Ministerio da "
            "Educacao. A sede fica em Brasilia, no Distrito Federal."
        )
        long_quote = (
            "A instituicao foi fundada em 15 de marco de 1985, como uma "
            "entidade sem fins lucrativos vinculada ao Ministerio da "
            "Educacao."
        )
        extractions = [
            {
                "provider": "gemini",
                "extraction": (
                    '[ALTA] A instituicao foi fundada em 1985 (especificamente em 15 '
                    'de marco de 1985). Trecho exato: "A instituicao foi fundada em '
                    '15 de marco de 1985"'
                ),
            },
            {
                "provider": "openrouter",
                "extraction": f'"{long_quote}" [ALTA]',
            },
            {
                "provider": "groq",
                "extraction": f'[ALTA] A instituicao foi fundada em 15 de marco de 1985. (Trecho: “{long_quote}”)',
            },
            {
                "provider": "mistral",
                "extraction": (
                    '1. **"A instituicao foi fundada em 15 de marco de 1985"** – *[ALTA]*\n'
                    f'   *Trecho exato:* *"{long_quote}"*\n\n'
                    '---\n'
                    '*Nota: outras informacoes nao respondem a pergunta.*'
                ),
            },
            {
                "provider": "cohere",
                "extraction": (
                    f'A instituicao foi fundada em 15 de marco de 1985. [ALTA] '
                    f'— trecho: “{long_quote}”'
                ),
            },
        ]
        result = cross_reference(extractions, material)
        verificados = [r for r in result if r["status"] == "VERIFICADO"]
        self.assertEqual(len(verificados), 1, f"esperava 1 VERIFICADO, veio: {result}")
        self.assertEqual(verificados[0]["confirmations"], 5)
        self.assertEqual(
            sorted(verificados[0]["sources"]),
            ["cohere", "gemini", "groq", "mistral", "openrouter"],
        )
        self.assertEqual(verificados[0]["claim"], long_quote)
        # o "---" e a nota lateral do mistral (sem aspas) viram fallback
        # NAO-VERIFICADO isolado, mas continuam presentes, não descartados
        nao_verificados = [r for r in result if r["status"] == "NAO-VERIFICADO"]
        self.assertTrue(any("Nota" in r["claim"] for r in nao_verificados))


class TestDispatch(unittest.TestCase):
    def test_material_file_not_found(self):
        result, code = dispatch(
            ["extract", "pergunta", "/caminho/inexistente.txt"], providers=FAKE_PROVIDERS,
        )
        self.assertEqual(code, 1)
        self.assertIn("not found", result["error"])

    def test_no_providers_returns_error(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("material de teste")
            path = f.name
        try:
            result, code = dispatch(["extract", "pergunta", path], providers=[])
            self.assertEqual(code, 1)
            self.assertIn("error", result)
        finally:
            os.remove(path)

    def test_unknown_stage(self):
        result, code = dispatch(["bogus", "pergunta", "/tmp/x.txt"], providers=FAKE_PROVIDERS)
        self.assertEqual(code, 1)
        self.assertIn("Unknown stage", result["error"])

    def test_success_path_returns_cross_reference(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("a empresa foi fundada em 2020.")
            path = f.name
        try:
            http_post = make_http_post({
                "https://fake/gemini": "[ALTA] a empresa foi fundada em 2020",
                "https://fake/groq": "[ALTA] a empresa foi fundada em 2020",
            })
            result, code = dispatch(
                ["extract", "quando foi fundada?", path],
                providers=FAKE_PROVIDERS, http_post=http_post,
            )
            self.assertEqual(code, 0)
            self.assertEqual(len(result["extractions"]), 2)
            self.assertEqual(result["cross_reference"][0]["status"], "VERIFICADO")
        finally:
            os.remove(path)

    def test_success_path_with_baixa_marker(self):
        """Teste que [BAIXA] é processado igual a [ALTA]."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("a empresa foi fundada em 2020.")
            path = f.name
        try:
            http_post = make_http_post({
                "https://fake/gemini": "[BAIXA] a empresa foi fundada em 2020",
                "https://fake/groq": "[BAIXA] a empresa foi fundada em 2020",
            })
            result, code = dispatch(
                ["extract", "quando foi fundada?", path],
                providers=FAKE_PROVIDERS, http_post=http_post,
            )
            self.assertEqual(code, 0)
            self.assertEqual(len(result["cross_reference"]), 1)
            self.assertEqual(result["cross_reference"][0]["status"], "VERIFICADO")
            self.assertEqual(result["cross_reference"][0]["confirmations"], 2)
        finally:
            os.remove(path)

    def test_extractions_preserve_raw_markers_but_cross_reference_cleans(self):
        """Verifica que result["extractions"] preserva marcadores brutos,
        mas cross_reference usa versão limpa."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("a empresa foi fundada em 2020.")
            path = f.name
        try:
            http_post = make_http_post({
                "https://fake/gemini": "[ALTA] a empresa foi fundada em 2020",
            })
            result, code = dispatch(
                ["extract", "quando foi fundada?", path],
                providers=[FAKE_PROVIDERS[0]], http_post=http_post,
            )
            self.assertEqual(code, 0)
            # Extractions preserves raw [ALTA] marker
            self.assertIn("[ALTA]", result["extractions"][0]["extraction"])
            # Cross-reference shows cleaned version as claim
            self.assertEqual(result["cross_reference"][0]["claim"], "a empresa foi fundada em 2020")
        finally:
            os.remove(path)

    def test_different_markers_same_claim_converge_in_cross_reference(self):
        """Teste caso real: gemini usa [ALTA], groq usa [BAIXA] para mesma
        afirmação — após limpeza, convergem e são VERIFICADO."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("a empresa foi fundada em 2020.")
            path = f.name
        try:
            http_post = make_http_post({
                "https://fake/gemini": "[ALTA] a empresa foi fundada em 2020",
                "https://fake/groq": "[BAIXA] a empresa foi fundada em 2020",
            })
            result, code = dispatch(
                ["extract", "quando foi fundada?", path],
                providers=FAKE_PROVIDERS, http_post=http_post,
            )
            self.assertEqual(code, 0)
            # Both extractions preserved as-is with their markers
            self.assertIn("[ALTA]", result["extractions"][0]["extraction"])
            self.assertIn("[BAIXA]", result["extractions"][1]["extraction"])
            # But cross-reference shows single unified claim with 2 confirmations
            self.assertEqual(len(result["cross_reference"]), 1)
            self.assertEqual(result["cross_reference"][0]["status"], "VERIFICADO")
            self.assertEqual(result["cross_reference"][0]["confirmations"], 2)
            self.assertEqual(sorted(result["cross_reference"][0]["sources"]), ["gemini", "groq"])
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
