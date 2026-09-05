#!/usr/bin/env python3
"""
council_free.py — free-tier cross-vendor LLM Council member calls.

Chama Gemini, OpenRouter, Groq, Mistral e Cohere (todos via endpoints
compatíveis com a API da OpenAI) para a Rodada 1 (respostas
independentes) e Rodada 2 (reação cruzada, após ver as respostas
anonimizadas dos outros membros). O assento do Claude-membro e a
síntese final do Claude-orquestrador ficam fora deste script — veja
SKILL.md.

Uso:
    python council_free.py round1 "pergunta"
    python council_free.py round2 "pergunta" round1_results.json

Lê as chaves de API do ambiente ou de ~/.claude/.env:
    GEMINI_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY,
    COHERE_API_KEY

Mistral e Cohere são opcionais (degradação graciosa igual aos outros
três — sem chave, o provedor simplesmente não entra na rodada).
Adicionados em 2026-09-04 para aumentar a diversidade de família de
modelo do painel. SambaNova foi avaliado e descartado no mesmo dia — a
conta gratuita exige cartão cadastrado (HTTP 402 confirmado ao vivo), o
que viola o princípio de "sem custo adicional" deste concílio; não
readicionar sem decisão explícita do usuário. GitHub Models também foi
avaliado e descartado — confirmado, ao checar a documentação oficial,
que o serviço foi inteiramente descontinuado em 30/07/2026.

**Nota sobre o modelo da Mistral:** o tier gratuito ("Free mode") tem
teto de taxa muito baixo por desenho — não é bug nem demora de
provisionamento. `mistral-large`/`mistral-medium`/`mistral-small`
voltaram 429 em toda tentativa de teste (múltiplas, ao longo de
minutos). `ministral-8b-latest` (modelo menor) foi testado ao vivo com
sucesso duas vezes seguidas — é o que está configurado abaixo. Se
voltar a dar 429 no uso real, considerar isso confirmação de que o
teto do tier gratuito realmente não comporta o padrão de uso do
concílio, não repetir a mesma aposta não verificada de novo — perguntar
ao usuário antes de trocar de modelo de novo.

Nomes de modelo de free-tier mudam com frequência nos provedores — se
um `model` abaixo passar a retornar 404, checar o catálogo atual do
provedor e atualizar aqui; o `failures` do dispatch já reporta isso
sem travar o
resto do painel.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

PROVIDERS = [
    {
        "name": "gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "api_key_env": "GEMINI_API_KEY",
        "model": "gemini-3.6-flash",
    },
    {
        "name": "openrouter",
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "api_key_env": "OPENROUTER_API_KEY",
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
    },
    {
        "name": "groq",
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "api_key_env": "GROQ_API_KEY",
        "model": "openai/gpt-oss-120b",
    },
    {
        "name": "mistral",
        "base_url": "https://api.mistral.ai/v1/chat/completions",
        "api_key_env": "MISTRAL_API_KEY",
        "model": "ministral-8b-latest",
    },
    {
        "name": "cohere",
        "base_url": "https://api.cohere.ai/compatibility/v1/chat/completions",
        "api_key_env": "COHERE_API_KEY",
        "model": "command-a-plus-05-2026",
    },
]

# sambanova ficou de fora (2026-09-04): testado ao vivo com a chave real
# do usuário e devolveu HTTP 402 PAYMENT_METHOD_REQUIRED — a conta exige
# cartão cadastrado mesmo pro saldo gratuito, o que viola o princípio de
# "sem custo adicional, nunca pede cartão" deste concílio (ver Global
# Constraints do plano original). Não readicionar sem o usuário decidir
# explicitamente que quer cadastrar cartão lá.

TIMEOUT = 120

QUALITY_INSTRUCTION = (
    "Responda passo a passo, de forma exaustiva. Declare suas premissas "
    "principais e a objeção mais forte à sua própria posição. Seja direto e "
    "específico — sem preâmbulo, sem hedging."
)


def load_api_key(env_var):
    val = os.environ.get(env_var)
    if val:
        return val.strip()
    for path in (os.path.join(os.getcwd(), ".env"),
                 os.path.expanduser("~/.claude/.env")):
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{env_var}="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            continue
    return None


def call_model(base_url, api_key, model, prompt, http_post=None):
    """Retorna (content, error). Exatamente um dos dois é não-None.

    http_post é um seam injetável para teste — por padrão faz um POST real
    via urllib. Deve aceitar (url, headers, body_bytes) e devolver o dict
    JSON decodificado, levantando urllib.error.HTTPError ou qualquer
    Exception em caso de falha.
    """
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    poster = http_post or _real_http_post
    try:
        data = poster(base_url, headers, body)
        return data["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        return None, f"HTTP {e.code}: {detail}"
    except Exception as e:  # noqa: BLE001 — repassar qualquer falha ao chamador
        return None, f"{type(e).__name__}: {e}"


def _real_http_post(url, headers, body):
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("User-Agent", "Mozilla/5.0")
    for k, v in headers.items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.load(resp)


def available_providers():
    """Provedores de PROVIDERS que têm chave de API disponível.

    Cada dict retornado é uma cópia da entrada em PROVIDERS mais a chave
    "api_key".
    """
    result = []
    for p in PROVIDERS:
        key = load_api_key(p["api_key_env"])
        if key:
            entry = dict(p)
            entry["api_key"] = key
            result.append(entry)
    return result


def run_round1(question, providers, http_post=None):
    """Chama cada provedor de forma independente. Retorna (members, failures)."""
    prompt = f"{QUALITY_INSTRUCTION}\n\nPergunta: {question}"

    def _call(p):
        content, err = call_model(p["base_url"], p["api_key"], p["model"], prompt, http_post)
        return p["name"], content, err

    with ThreadPoolExecutor(max_workers=max(len(providers), 1)) as ex:
        results = list(ex.map(_call, providers))

    members, failures = [], []
    for name, content, err in results:
        if err:
            failures.append({"provider": name, "error": err})
        else:
            members.append({"provider": name, "answer": content})
    return members, failures


def build_round2_prompt(question, own_provider, round1_members):
    """Prompt mostrado a `own_provider`: respostas dos outros, anonimizadas."""
    others = [m for m in round1_members if m["provider"] != own_provider]
    labels = [chr(ord("A") + i) for i in range(len(others))]
    block = "\n\n".join(
        f"Resposta {label}:\n{m['answer']}"
        for label, m in zip(labels, others)
    )
    return (
        f"{QUALITY_INSTRUCTION}\n\n"
        f"Pergunta original: {question}\n\n"
        f"Sua resposta independente já foi registrada. Aqui estão as respostas "
        f"anonimizadas de outros membros do conselho:\n\n{block}\n\n"
        "Reaja: concorde, discorde ou ajuste sua posição original, sendo "
        "explícito sobre o que mudou e por quê. Se nada mudou, diga por quê "
        "sua posição resiste às outras."
    )


def run_round2(question, providers, round1_members, http_post=None):
    """Cada provedor reage às respostas de Rodada 1 dos outros membros."""
    def _call(p):
        prompt = build_round2_prompt(question, p["name"], round1_members)
        content, err = call_model(p["base_url"], p["api_key"], p["model"], prompt, http_post)
        return p["name"], content, err

    with ThreadPoolExecutor(max_workers=max(len(providers), 1)) as ex:
        results = list(ex.map(_call, providers))

    members, failures = [], []
    for name, content, err in results:
        if err:
            failures.append({"provider": name, "error": err})
        else:
            members.append({"provider": name, "reaction": content})
    return members, failures


def dispatch(argv, providers=None, http_post=None):
    """Executa um estágio (round1/round2) e retorna (result_dict, exit_code)."""
    if len(argv) < 2:
        return {"error": "Usage: council_free.py <round1|round2> <question> [round1_results.json]"}, 1

    stage, question = argv[0], argv[1]
    provs = providers if providers is not None else available_providers()

    if not provs:
        return {"error": "No provider API keys found. Set GEMINI_API_KEY, "
                          "OPENROUTER_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY "
                          "and/or COHERE_API_KEY in the environment or "
                          "~/.claude/.env."}, 1

    if stage == "round1":
        members, failures = run_round1(question, provs, http_post)
        return {"members": members, "failures": failures}, 0

    if stage == "round2":
        if len(argv) < 3:
            return {"error": "round2 requires a round1_results.json path"}, 1
        try:
            with open(argv[2], encoding="utf-8") as f:
                round1_members = json.load(f)["members"]
        except FileNotFoundError:
            return {"error": f"round1_results.json not found: {argv[2]}"}, 1
        except json.JSONDecodeError as e:
            return {"error": f"round1_results.json is not valid JSON: {e}"}, 1
        except KeyError:
            return {"error": f"round1_results.json is missing a 'members' key: {argv[2]}"}, 1
        members, failures = run_round2(question, provs, round1_members, http_post)
        return {"members": members, "failures": failures}, 0

    return {"error": f"Unknown stage '{stage}'. Use round1 or round2."}, 1


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result, code = dispatch(sys.argv[1:])
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(code)


if __name__ == "__main__":
    main()
