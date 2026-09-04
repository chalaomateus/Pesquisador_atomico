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

## Instalação (Claude Code)

Copie `pesquisador.md` para `~/.claude/agents/pesquisador.md` (ou
`.claude/agents/` do seu projeto). Requer as tools `WebSearch`,
`WebFetch` e `Bash` liberadas para o agente.

Fontes que exigem chave (opcionais, o agente funciona sem elas —
menos essas fontes ficam indisponíveis):
- Reddit: `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` (OAuth2)

## Licença

MIT
