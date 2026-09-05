# Pesquisador Atômico

Agente customizado para o Claude Code que decompõe qualquer pergunta de
pesquisa em unidades atômicas — afirmações verificáveis isoladamente —
antes de buscar qualquer coisa. Cada unidade recebe fonte apropriada,
é triangulada com peso de fonte (não só contagem), e recebe um veredito
próprio (CONFIRMADO / DERRUBADO / INCONCLUSIVO) antes da síntese final.

## Por que "atômico"

A maioria dos agentes de busca trata a pergunta como um bloco só e
devolve uma resposta genérica confiante, mesmo quando parte dela não
foi verificada. Este agente força a decomposição primeiro: uma pergunta
como "X é mais rápido que Y e tem suporte a TypeScript?" vira duas
unidades independentes, cada uma resolvida e rotulada separadamente.

## Como funciona

1. **Decompõe** a pergunta em unidades atômicas verificáveis
2. **Escolhe a fonte certa por unidade** — Google, Wikipedia, Hacker
   News, Stack Overflow ou Reddit, conforme o tipo de pergunta
3. **Triangula com peso de fonte**, não só contagem — fórum/rede social
   nunca confirma fato sozinho
4. **Registra veredito por unidade** antes de montar a síntese final
5. Nunca cita URL que não veio literalmente de uma chamada de
   ferramenta na sessão (evita alucinação de link)

## Esquadrão de minions (checagem cruzada com múltiplas LLMs)

Para unidades atômicas de maior risco — pessoa/empresa/entidade
específica, material bruto longo ou vindo de várias páginas, ou a
pedido explícito do usuário — o agente pode acionar um "esquadrão de
minions": até 5 LLMs gratuitas (Gemini, OpenRouter, Groq, Mistral,
Cohere) recebem em paralelo a mesma sub-pergunta e o material bruto já
coletado, e cada uma extrai independentemente só o que está
literalmente presente no texto — nunca completando com conhecimento
próprio, nunca inferindo além do que está escrito. O próprio
Pesquisador (o "Gru" do esquadrão) cruza as extrações: uma afirmação
confirmada por 2 ou mais minions **e** rastreável a um trecho real do
material vira `VERIFICADO`; o resto aparece como `NÃO-VERIFICADO` —
mostrado na resposta final, nunca descartado silenciosamente.

- Reaproveita a mesma infraestrutura de degradação graciosa do skill
  `llm-council` (falta de chave numa API não trava as outras; se zero
  minions responderem, o agente cai de volta no fluxo normal — a
  camada é aditiva, nunca uma dependência dura).
- Ativação é opcional e por unidade — não dispara em toda busca
  simples, só nos casos de risco de alucinação mais alto.
- Validado com testes unitários (mocks, sem chamada de rede real) e
  com um teste real de ponta a ponta antes de ser considerado pronto —
  esse teste ao vivo revelou 2 rodadas de bugs reais, corrigidos antes
  da funcionalidade ser declarada concluída. Não é um detalhe pra
  esconder: é a mesma disciplina de "nunca declarar pronto sem rodar
  de verdade" aplicada em todo o projeto.

## Navegador remoto (Browserbase) — o diferencial deste agente

Quando uma fonte bloqueia scraping comum (Cloudflare, detecção de
automação, JS pesado), o Pesquisador escala para um navegador Chromium
**real**, rodando na infraestrutura da Browserbase — não é spoofing de
header, é sessão de navegador de verdade, com fingerprint que os
próprios serviços de bot-detection reconhecem como legítimo. Isso
destrava fontes que travam tanto `curl`/`curl_cffi` quanto Playwright
local (que carrega fingerprint de automação detectável).

- **Ordem de escalada** (Browserbase nunca é a primeira tentativa):
  `WebFetch`/`curl` → `curl_cffi` → Playwright local → Browserbase —
  só sobe de degrau quando o anterior falha de verdade.
- Free tier: 1h de navegador por mês, sessão de até 15 minutos — por
  isso não é acionado "pra garantir", só quando é realmente necessário.
- Tem proxy residencial/datacenter disponível para bloqueio por
  IP/geolocalização.
- **Nunca aciona o auto-solver de captcha de verdade (hCaptcha/
  reCAPTCHA) sem confirmar com o usuário antes** — bloqueio anti-bot
  genérico é uma categoria diferente de captcha real, e essa distinção
  nunca é resolvida silenciosamente só porque a ferramenta permite.

## Instalação (Claude Code)

Copie `pesquisador.md` para `~/.claude/agents/pesquisador.md` (ou
`.claude/agents/` do seu projeto). Requer as tools `WebSearch`,
`WebFetch` e `Bash` liberadas para o agente.

Fontes que exigem chave (opcionais, o agente funciona sem elas —
menos essas fontes ficam indisponíveis):
- Reddit: `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` (OAuth2)

Recursos avançados (opcionais, cada um com sua própria dependência):
- **Esquadrão de minions**: os scripts já estão inclusos neste
  repositório em [`scripts/minions_extract.py`](scripts/minions_extract.py)
  e [`scripts/council_free.py`](scripts/council_free.py) — nenhuma
  instalação extra além de copiar a pasta `scripts/` junto com
  `pesquisador.md`. Configure ao menos uma chave de API entre
  `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`,
  `MISTRAL_API_KEY` ou `COHERE_API_KEY` — como variável de ambiente ou
  num arquivo `~/.claude/.env` (`NOME_DA_CHAVE=valor`, uma por linha).
  Para rodar a extração isoladamente, fora do agente:
  ```
  python scripts/minions_extract.py extract "<pergunta>" "<caminho .txt do material bruto>"
  ```
  Para rodar o conselho de LLMs isoladamente:
  ```
  python scripts/council_free.py round1 "<pergunta>"
  ```
  Para rodar os testes (não precisa de nenhuma chave — usam mocks):
  ```
  cd scripts && python -m unittest discover -v
  ```
- **Browserbase**: precisa do servidor MCP `browserbase` configurado
  (`claude mcp add --transport http`) e de uma conta/API key da
  Browserbase.

## Licença

MIT
