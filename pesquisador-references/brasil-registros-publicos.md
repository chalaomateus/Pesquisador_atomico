# Fontes extras — pessoa/empresa/registro público do Brasil

Quando a unidade atômica for sobre pessoa física, empresa ou entidade
brasileira (não é o caso padrão — só ativa quando fizer sentido pro que
está sendo perguntado):

- **Querido Diário** (Open Knowledge Brasil, gratuito, sem chave) —
  busca de texto em diários oficiais municipais:
  `https://api.queridodiario.org.br/gazettes?querystring=<termo>&size=<N>`
  (busca é aproximada, não exata — confirme o excerto antes de citar
  como achado; cobertura é parcial, nem todo município brasileiro está
  indexado — confira em `https://api.queridodiario.org.br/cities` se o
  município que importa está coberto e desde quando, antes de tratar
  resultado zero como "não existe menção", pode só ser "não indexado
  ainda"). **Atenção: o domínio antigo `api.queridodiario.ok.org.br`
  não serve mais a API (fica de pé mas fecha a conexão) — usar sempre
  `api.queridodiario.org.br`, sem o `.ok.`.**
- **Portal da Transparência / CGU** (gratuito, precisa de chave — pedir
  em `portaldatransparencia.gov.br/api-de-dados/cadastrar-email`, já
  configurada como `PORTAL_TRANSPARENCIA_API_KEY` no `.env`) — sanções
  federais e impedimentos por CPF/CNPJ:
  `curl -H "chave-api-dados: $PORTAL_TRANSPARENCIA_API_KEY"
  "https://api.portaldatransparencia.gov.br/api-de-dados/ceis?codigoSancionado=<CPF/CNPJ sem pontuação>"`
  (troque `ceis` por `cnep` pra outro cadastro de sanção; resultado
  `[]` é achado real — "sem sanção encontrada", não erro).
- **BrasilAPI** (comunidade, sem chave, grátis) — agregador de dados
  públicos brasileiros num só lugar: CEP, CNPJ (mesma fonte da Receita
  Federal), bancos, feriados, DDD, tabela FIPE de veículos, entre
  outros: `https://brasilapi.com.br/api/<recurso>/v1/<parametro>` (ex.:
  `https://brasilapi.com.br/api/cep/v1/01310930`,
  `https://brasilapi.com.br/api/cnpj/v1/<CNPJ sem pontuação>`). Testado
  ao vivo em 2026-09-15 (HTTP 200, dado real). Boa primeira parada antes
  de recorrer a serviço específico — cobre vários tipos de unidade
  atômica (endereço, empresa, veículo) com uma única fonte.
- **ReceitaWS** (sem chave, grátis) — consulta situação cadastral de
  CNPJ direto na base da Receita Federal:
  `https://www.receitaws.com.br/v1/cnpj/<CNPJ sem pontuação>`. Retorna
  razão social, situação (ativa/baixada), CNAE, sócios (quando
  disponíveis) e data de abertura. **Rate limit do plano grátis é curto
  (3 consultas/minuto)** — espaçar chamadas em consulta de várias
  empresas seguidas. Testado ao vivo em 2026-09-15 com CNPJ real (Banco
  do Brasil), retornou dado correto.
- **Radar CNPJ** (sem chave, grátis) — alternativa mais recente à
  ReceitaWS, também consulta e monitora CNPJ, feita explicitamente para
  uso por agente de IA: `https://radar-cnpj.com/api/` (documentação em
  `llms.txt`/`llms-full.txt` na raiz do domínio). Testado ao vivo em
  2026-09-15.
- **ViaCEP** (sem chave, grátis, referência clássica) — endereço
  completo a partir de CEP brasileiro:
  `https://viacep.com.br/ws/<CEP>/json/`. Útil pra confirmar/enriquecer
  endereço de pessoa/empresa antes de cruzar com outra fonte (Portal da
  Transparência, Google Maps). Testado ao vivo em 2026-09-15.
- **IBGE — Serviço de Dados** (sem chave, grátis, fonte oficial) —
  dados geográficos e demográficos do Instituto Brasileiro de Geografia
  e Estatística (municípios, estados, população, PIB per capita etc.):
  `https://servicodados.ibge.gov.br/api/v1/localidades/estados` (outros
  recursos em `servicodados.ibge.gov.br/api/docs`). Testado ao vivo em
  2026-09-15.
- **Banco Central do Brasil — Dados Abertos** (sem chave, grátis, fonte
  oficial) — indicadores econômicos e financeiros oficiais (câmbio,
  taxas, séries temporais): `https://dadosabertos.bcb.gov.br/`.
  Complementa o Portal da Transparência (sanção/impedimento) com dado
  macro/financeiro oficial. Testado ao vivo em 2026-09-15.
