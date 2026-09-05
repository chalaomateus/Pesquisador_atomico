#!/usr/bin/env python3
"""
minions_extract.py — esquadrão de minions do Pesquisador.

Reaproveita os provedores gratuitos já configurados em council_free.py
(mesmo diretório) para extrair, em paralelo, afirmações literalmente
presentes num material bruto já coletado pelo Pesquisador — e cruza as
extrações dos minions pra marcar o que está confirmado por mais de um vs.
o que não está (ver cross_reference()).

Uso:
    python minions_extract.py extract "<sub-pergunta>" "<caminho .txt do material bruto>"

**Verificação real de ponta a ponta (2026-09-05):** rodado ao vivo (sem
mock) contra os 5 provedores de council_free.py, com material factual
real (trecho sobre a fundação/sede da Embraer, coletado via WebFetch da
Wikipédia) e uma pergunta real sobre esse material. Os 5 provedores
responderam com sucesso — gemini, openrouter, groq, mistral e cohere
todos em `extractions`, `failures` vazio. Nenhum precisou de ajuste de
modelo/endpoint nesta rodada (os mesmos modelos já configurados em
PROVIDERS funcionaram de primeira). O conteúdo extraído por todos foi
coerente com o material, cada um citando o trecho exato correto — sem
sinal de alucinação.

Na primeira rodada dessa verificação, `cross_reference` marcou todas as
afirmações como NAO-VERIFICADO apesar dos 5 provedores concordarem no
fato — cada um formatava a linha de um jeito diferente (aspas retas vs.
curvas, "Trecho exato:" vs "— trecho:", numeração/markdown do Mistral,
posição do marcador [ALTA]) e a comparação de então era pela LINHA
inteira, não pela citação. Corrigido no mesmo dia: `cross_reference`
agora extrai a citação entre aspas de cada linha (QUOTE_RE, cobre aspas
retas e curvas) e agrupa por sobreposição de substring bidirecional — a
citação curta de um provedor (só a data) e a citação longa de outro (a
frase inteira) convergem no mesmo grupo. Linha sem nenhuma citação cai
no comportamento antigo (linha inteira, comparação exata). Re-executado
ao vivo contra o mesmo material da Embraer após a correção: os 2 fatos
reais (data de fundação, sede) agora saem VERIFICADO com
confirmations=5 (os 5 provedores).
"""
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from council_free import available_providers, call_model  # noqa: E402

# Casa citação entre aspas retas ("...") OU curvas ("..."/"...") — os 5
# provedores reais usam ambos os estilos (ver docstring de cross_reference()).
QUOTE_RE = re.compile(r'["“]([^"“”]+)["”]')

# Comprimento mínimo (chars normalizados) para uma citação poder "pontear"
# grupos por containment assimétrico — ver docstring de cross_reference()
# e os dois casos adversariais (endereço/data, "gato fabricado") que
# motivaram essa salvaguarda. "19 de agosto de 1969" tem exatamente 20
# chars normalizados — o menor trecho fatual real observado nos 5
# provedores da Task 4 — por isso o limiar fica nesse valor: protege
# contra citação-isolada-vira-ponte sem cortar o caso real que a correção
# original precisava resolver.
MIN_BRIDGE_LEN = 20


def _quotes_match(norm_a, norm_b):
    """True se duas citações normalizadas (já em minúsculo/espaços
    colapsados) contam como a mesma afirmação.

    Igualdade exata sempre conta. Containment bidirecional (uma é
    substring da outra) só conta quando AMBAS têm pelo menos
    MIN_BRIDGE_LEN caracteres — uma citação curta ("1969", "o gato
    correu") não pode servir de ponte entre duas citações longas e
    distintas só por ser substring das duas (ver docstring de
    cross_reference()).
    """
    if norm_a == norm_b:
        return True
    if len(norm_a) < MIN_BRIDGE_LEN or len(norm_b) < MIN_BRIDGE_LEN:
        return False
    return norm_a in norm_b or norm_b in norm_a

# Confidence markers recognized in extraction output by run_extraction() and cleaned by dispatch()
CONFIDENCE_MARKERS = {"[ALTA]": 6, "[BAIXA]": 7}  # marker -> prefix length

EXTRACTION_PROMPT_TEMPLATE = (
    "Você vai receber uma pergunta e um material bruto coletado da web.\n\n"
    "Pergunta: {question}\n\n"
    "Material bruto:\n{material}\n\n"
    "Extraia SOMENTE afirmações que estão literalmente presentes no material "
    "acima — para cada uma, cite o trecho exato de onde veio. Nunca complete "
    "com conhecimento próprio, nunca infira além do que está escrito. Se o "
    "material não responder a pergunta, diga isso explicitamente em vez de "
    "inventar. Marque cada afirmação extraída com [ALTA] ou [BAIXA] "
    "confiança, conforme o quanto o trecho é direto/inequívoco. Uma "
    "afirmação por linha."
)


def build_extraction_prompt(question, material):
    return EXTRACTION_PROMPT_TEMPLATE.format(question=question, material=material)


def run_extraction(question, material, providers, http_post=None):
    """Chama cada provedor em paralelo para extrair fatos do material.

    Retorna (extractions, failures) — mesmo formato members/failures já
    usado em council_free.py.
    """
    prompt = build_extraction_prompt(question, material)

    def _call(p):
        content, err = call_model(p["base_url"], p["api_key"], p["model"], prompt, http_post)
        return p["name"], content, err

    with ThreadPoolExecutor(max_workers=max(len(providers), 1)) as ex:
        results = list(ex.map(_call, providers))

    extractions, failures = [], []
    for name, content, err in results:
        if err:
            failures.append({"provider": name, "error": err})
        else:
            extractions.append({"provider": name, "extraction": content})
    return extractions, failures


def cross_reference(extractions, material, min_confirmations=2):
    """Cruza as extrações dos minions.

    O prompt pede que cada afirmação venha com "o trecho exato" entre
    aspas (ver EXTRACTION_PROMPT_TEMPLATE) — é essa citação, não a linha
    inteira, que vira a chave de agrupamento (QUOTE_RE casa aspas retas
    "..." e curvas “.../”...). Duas citações contam como a mesma
    afirmação se, normalizadas (minúsculo, espaços colapsados), forem
    idênticas OU uma for substring da outra — mas o containment
    (substring) só vale entre citações com pelo menos MIN_BRIDGE_LEN
    caracteres (ver _quotes_match()). Isso corrige o bug real encontrado
    na verificação ao vivo da Task 4 (Embraer, 2026-09-05): os 5
    provedores concordavam no fato mas formatavam a linha de um jeito
    diferente cada (posição do marcador [ALTA]/[BAIXA], "Trecho exato:"
    vs "— trecho:", markdown do Mistral) — comparar a LINHA inteira nunca
    batia confirmations >= 2 na prática, mesmo com concordância real. O
    grupo de citações equivalentes guarda a mais longa (mais informativa)
    como "claim" no resultado.

    **Duas salvaguardas contra falso-positivo, adicionadas depois que o
    revisor demonstrou os dois casos abaixo contra a v1 desta correção:**

    1. *Citação curta não pontea grupos distintos.* Ex.: "1969" isolado
       é substring tanto de "a empresa foi fundada em 1969 no Brasil"
       quanto de "a sede fica na Rua 1969, no bairro Central" — sem
       limiar de comprimento, os 3 se fundiam num grupo só e reportavam
       "confirmado por 3" para 2 fatos DIFERENTES, cada um confirmado por
       apenas 1 provedor de verdade. MIN_BRIDGE_LEN=20 impede isso: abaixo
       do limiar, só igualdade exata conta (duas citações curtas
       idênticas, como duas datas iguais, ainda convergem).

    2. *`traceable` usa só o claim exibido, não qualquer citação do
       grupo.* Ex. mais grave: um provedor cita "o gato correu" (real),
       outro "estende" com "o gato correu voando pelo ceu ateh a lua"
       (fabricado, não está no material) — o trecho real é substring do
       fabricado, então v1 os fundia e considerava o grupo "rastreável"
       porque ALGUMA citação do grupo (a real, curta) batia no material,
       exibindo o texto alucinado como VERIFICADO. Agora `traceable`
       checa só `g["longest_norm"]` (o que de fato vira "claim" no
       retorno) contra o material — o texto fabricado, sendo mais longo
       e não literal, falha essa checagem. Combinada com a salvaguarda 1
       (que já impede boa parte desses casos de nem se fundirem), reduz o
       risco de alucinação sair etiquetada como fato verificado.

    Linha sem NENHUMA citação entre aspas (modelo não seguiu o formato
    pedido) cai no comportamento antigo: a linha inteira normalizada vira
    a chave, comparada por igualdade exata (não fuzzy) — mesma limitação
    de sempre pra esse caso, mas nunca descartada.

    Uma afirmação vira VERIFICADO quando (a) aparece em min_confirmations
    ou mais provedores distintos E (b) o claim exibido (a citação mais
    longa do grupo) é substring do material normalizado (rastreável a um
    trecho real). Senão, NAO-VERIFICADO — mas sempre presente no retorno.
    """
    def normalize(text):
        return " ".join(text.strip().lower().split())

    quote_groups = []  # [{"norms": set(), "longest": str, "longest_norm": str, "providers": set()}]
    fallback_claims = {}  # normalized whole line -> {"original": str, "providers": set()}

    for e in extractions:
        for line in e["extraction"].splitlines():
            line = line.strip()
            if not line:
                continue
            quotes = [q.strip() for q in QUOTE_RE.findall(line) if q.strip()]
            if not quotes:
                norm = normalize(line)
                if norm not in fallback_claims:
                    fallback_claims[norm] = {"original": line, "providers": set()}
                fallback_claims[norm]["providers"].add(e["provider"])
                continue
            for quote in quotes:
                norm = normalize(quote)
                matched_idxs = [
                    i for i, g in enumerate(quote_groups)
                    if any(_quotes_match(norm, gn) for gn in g["norms"])
                ]
                if not matched_idxs:
                    quote_groups.append({
                        "norms": {norm},
                        "longest": quote,
                        "longest_norm": norm,
                        "providers": {e["provider"]},
                    })
                    continue
                primary = quote_groups[matched_idxs[0]]
                for idx in matched_idxs[1:]:
                    other = quote_groups[idx]
                    primary["norms"] |= other["norms"]
                    primary["providers"] |= other["providers"]
                    if len(other["longest_norm"]) > len(primary["longest_norm"]):
                        primary["longest"] = other["longest"]
                        primary["longest_norm"] = other["longest_norm"]
                if len(matched_idxs) > 1:
                    drop = set(matched_idxs[1:])
                    quote_groups = [g for i, g in enumerate(quote_groups) if i not in drop]
                primary["norms"].add(norm)
                primary["providers"].add(e["provider"])
                if len(norm) > len(primary["longest_norm"]):
                    primary["longest"] = quote
                    primary["longest_norm"] = norm

    material_norm = normalize(material)
    results = []
    for g in quote_groups:
        confirmations = len(g["providers"])
        traceable = g["longest_norm"] in material_norm
        status = "VERIFICADO" if (confirmations >= min_confirmations and traceable) else "NAO-VERIFICADO"
        results.append({
            "claim": g["longest"],
            "status": status,
            "confirmations": confirmations,
            "sources": sorted(g["providers"]),
        })
    for norm, data in fallback_claims.items():
        confirmations = len(data["providers"])
        traceable = norm in material_norm
        status = "VERIFICADO" if (confirmations >= min_confirmations and traceable) else "NAO-VERIFICADO"
        results.append({
            "claim": data["original"],
            "status": status,
            "confirmations": confirmations,
            "sources": sorted(data["providers"]),
        })
    return results


def dispatch(argv, providers=None, http_post=None):
    """Executa o estágio 'extract' e retorna (result_dict, exit_code)."""
    if len(argv) < 3:
        return {"error": "Usage: minions_extract.py extract <pergunta> <caminho_material.txt>"}, 1

    stage, question, material_path = argv[0], argv[1], argv[2]
    if stage != "extract":
        return {"error": f"Unknown stage '{stage}'. Use extract."}, 1

    try:
        with open(material_path, encoding="utf-8") as f:
            material = f.read()
    except FileNotFoundError:
        return {"error": f"Material file not found: {material_path}"}, 1

    provs = providers if providers is not None else available_providers()
    if not provs:
        return {"error": "No provider API keys found. Set GEMINI_API_KEY, "
                        "OPENROUTER_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY "
                        "and/or COHERE_API_KEY in the environment or "
                        "~/.claude/.env."}, 1

    extractions, failures = run_extraction(question, material, provs, http_post)

    # Remove confidence markers from extractions for cross-reference (see CONFIDENCE_MARKERS)
    cleaned_extractions = []
    for e in extractions:
        lines = []
        for line in e["extraction"].splitlines():
            line = line.strip()
            # Strip recognized confidence markers from line start
            for marker, marker_len in CONFIDENCE_MARKERS.items():
                if line.startswith(marker):
                    line = line[marker_len:].strip()
                    break
            if line:
                lines.append(line)
        cleaned_extractions.append({
            "provider": e["provider"],
            "extraction": "\n".join(lines)
        })

    crossed = cross_reference(cleaned_extractions, material) if cleaned_extractions else []
    return {"extractions": extractions, "failures": failures, "cross_reference": crossed}, 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result, code = dispatch(sys.argv[1:])
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(code)


if __name__ == "__main__":
    main()
