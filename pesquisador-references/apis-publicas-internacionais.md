# APIs públicas internacionais — OSINT, sanções, cripto, infraestrutura

Curadoria extraída do repositório `public-apis/public-apis` (GitHub,
~745 entradas revisadas em 16 categorias relevantes, 2026-09-15).
Complementa `brasil-registros-publicos.md` (registros brasileiros) e
`ferramentas-curadas.md` (ferramentas fora do fluxo padrão de busca).
Ativar quando a unidade atômica envolver empresa/pessoa/ativo fora do
escopo brasileiro, sanção internacional, rastreamento de criptoativo, ou
reconhecimento de infraestrutura técnica de uma empresa investigada.

- **OpenSanctions** (sem chave pra busca hospedada, grátis) — base
  consolidada de sanções internacionais (OFAC, UE, ONU), PEP (pessoa
  politicamente exposta) e crime organizado, agregando dezenas de listas
  oficiais num schema único: `https://www.opensanctions.org/docs/api/`
  — busca via `https://api.opensanctions.org/search/default?q=<nome>`.
  Referência padrão-ouro pra due diligence — usar sempre que a unidade
  atômica for "essa pessoa/empresa está sancionada ou é PEP". Testado ao
  vivo em 2026-09-15.
- **Wayback Machine / Archive.org** (sem chave, grátis) — snapshot
  histórico de qualquer URL, útil pra ver como um site (empresa, perfil,
  notícia) estava antes de ser editado ou removido:
  `https://archive.org/wayback/available?url=<url>` retorna o snapshot
  mais próximo disponível. Testado ao vivo em 2026-09-15, retornou
  snapshot real de exemplo.
- **Wikidata** (sem chave pra leitura, grátis) — base de conhecimento
  estruturada (entidade → propriedade → valor), complementa a Wikipedia
  já usada como fonte padrão quando a unidade pede dado estruturado
  (data de fundação, relação já catalogada entre entidades):
  `https://www.wikidata.org/w/api.php?action=wbsearchentities&search=<termo>&language=pt&format=json`.
  Testado ao vivo em 2026-09-15.
- **SEC EDGAR** (sem chave, grátis, exige só header `User-Agent`
  identificável — ex. `"NomeDoApp email@dominio.com"`) — filings e
  dados financeiros de empresas de capital aberto nos EUA:
  `https://data.sec.gov/submissions/CIK<10 dígitos>.json`. Útil quando a
  investigação envolve empresa americana com ações negociadas em bolsa.
  Testado ao vivo em 2026-09-15.
- **Blockchain.com API + Mempool.space + Ethplorer** (sem chave — ou
  chave pública gratuita no caso do Ethplorer, `apiKey=freekey`) — trio
  pra rastrear ativo em criptomoeda dentro de investigação patrimonial:
  `https://blockchain.info/rawaddr/<endereço BTC>` e
  `https://mempool.space/api/...` pro lado Bitcoin,
  `https://api.ethplorer.io/getAddressInfo/<endereço>?apiKey=freekey`
  pro lado Ethereum (saldo, histórico de transação, tokens). Os três
  testados ao vivo em 2026-09-15, retornaram dado real.
- **FBI Wanted** (sem chave, grátis) — lista de procurados pelo FBI,
  útil em checagem de antecedente de pessoa com atuação nos EUA:
  `https://api.fbi.gov/wanted/v1/list`. Testado ao vivo em 2026-09-15,
  retornou 1.244 registros reais.
- **Shodan** (conta grátis sem cartão, 10.000 créditos/mês) — motor de
  busca de dispositivo/servidor conectado à internet; útil pra
  reconhecimento de infraestrutura técnica exposta de uma empresa
  investigada (servidor mal configurado, porta aberta, versão de
  software desatualizada como indício de negligência de segurança):
  `https://developer.shodan.io/api` — precisa cadastro em
  `account.shodan.io/register` pra pegar a chave (não configurado ainda
  neste ambiente). **Limitação do plano grátis: sem filtro de busca
  avançado**, só consulta direta por IP/host.
- **Disify** (sem chave, grátis) — detecta se um e-mail é descartável ou
  temporário (sinal de perfil falso/fraude quando associado a uma
  pessoa/empresa investigada): `https://disify.com/api/email/<endereço>`
  (usar sem `www.`, que redireciona). Testado ao vivo em 2026-09-15.

## Incerto — candidato, mas com ressalva relevante

- **OpenCorporates** — referência clássica de registro societário
  global, mas o free tier (50 consultas/dia, 200/mês) só vale pra uso
  não-comercial com dado publicado sob licença aberta share-alike; uso
  comercial provavelmente exige plano pago. Vale usar se o caso
  permitir aplicar como jornalista/ONG, ou se topar pagar — não
  entra como padrão grátis.
- **Censys** — parecido com Shodan (reconhecimento de infraestrutura),
  free tier de 250 consultas/mês; não confirmei se o cadastro pede
  cartão de crédito, fica pendente de teste antes de virar padrão.
- **Interpol Red Notices** — API real e documentada
  (`ws-public.interpol.int/notices/v1/red`), mas bloqueou a chamada
  direta e com header de navegador (`Access Denied`, borda Akamai) a
  partir deste ambiente — pode ser bloqueio por IP de datacenter, não
  confirmo que funciona de fato na prática.
- **HaveIBeenPwned** — ficou pago desde 2024 pra busca de e-mail/domínio
  específico (a partir de ~US$4,39/mês); só o catálogo geral de
  vazamentos (`/breaches`) continua grátis sem chave — não serve pra
  checar exposição de uma pessoa específica, que é o uso real que
  importaria. Não passa no critério "grátis de verdade".
- **Numverify / apilayer** — validação de telefone com free tier
  histórico, hoje mediado pela APILayer (patrocinadora do próprio
  repositório) — não testei se o cadastro exige cartão.
- **PontoFato** — CEP + empresas registradas no mesmo endereço (útil pra
  achar fachada/coworking, mesmo conceito do truque de Google Maps já em
  `ferramentas-curadas.md`), mas é serviço pequeno/novo sem histórico —
  reavaliar se aparecer necessidade real.

## Não bate — fora de escopo ou eticamente problemático

- **CPFHub** — retorna nome completo, data de nascimento e gênero de
  qualquer CPF brasileiro. Mesmo alegando conformidade LGPD (segundo a
  própria página do produto — fonte não independente), é serviço
  comercial (`apiKey`) voltado a KYC empresarial: não é gratuito, e fazer
  lookup reverso de CPF de terceiro sem base legal específica do caso é
  terreno eticamente/legalmente arriscado demais pra virar ferramenta
  padrão (diferente de fonte de dado aberto institucional como
  BrasilAPI/Portal da Transparência).
- Maioria de **Business** (Mailchimp, Trello, Square etc.) — SaaS de
  produtividade/marketing, não serve pra OSINT/investigação.
- Maioria de **News** (GNews, NewsData, Currents etc.) — freemium
  redundante com o Google/WebSearch que o Pesquisador já usa como fonte
  padrão; não acrescenta capacidade nova o bastante pra justificar mais
  uma chave de API.
- Maioria de **Social** — já coberto por `redes-sociais-comentarios.md`
  (YouTube oficial) ou bloqueado por ToS (Instagram/X, já tratado ali).
  **Bluesky** é tecnicamente aberto (protocolo AT, sem ToS anti-scraping
  como Instagram/X) mas de baixa relevância de uso real no Brasil hoje —
  fica de vigia, não vira padrão agora.
- **Cryptocurrency exchanges** (Binance, Coinbase, Kraken etc.) — são
  plataformas de trading, não de rastreamento forense de endereço; já
  coberto pelo trio Blockchain.com/Mempool.space/Ethplorer acima.
- **Vehicle, Transportation, Patent, Phone** (exceto o já citado) —
  nichos com relevância só pontual e nenhuma opção grátis forte o
  bastante hoje pra virar padrão; reavaliar sob demanda de caso
  específico.
