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
