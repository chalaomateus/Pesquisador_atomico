# Ferramentas extras curadas — instaladas ou documentadas

- **Sherlock** (instalado, `python -m sherlock_project <username>`) —
  checa se um username existe em 400+ redes/sites, roda local, grátis,
  sem limite. Use pra unidade atômica tipo "esse nome de usuário
  aparece em outra rede social". **Nota de ToS a repassar sempre que
  usar:** Instagram/Facebook, LinkedIn, X e TikTok proíbem
  explicitamente, nos próprios Termos de Uso, "coleta de dados por
  meios automatizados sem permissão prévia" — mesmo pra checagem de
  existência (não extrai conteúdo privado, só confirma se o link
  resolve). Não é motivo pra recusar rodar em contexto profissional
  legítimo (isso o usuário decide), mas sempre mencionar o fato do ToS
  junto do resultado, não esconder.
- **Kaggle** (sem pacote instalado — API direta via `curl` é mais leve
  que o CLI oficial, que tem cadeia de dependência grande) — pra listar
  datasets: `curl -u "$KAGGLE_USERNAME:$KAGGLE_KEY"
  "https://www.kaggle.com/api/v1/datasets/list?search=<termo>"` (exige
  usuário/token da conta Kaggle pessoal de quem for usar — ainda não
  configurado, pedir quando for a primeira vez que fizer falta).
- **Google Alerts** — não é API, é serviço web
  (`google.com/alerts`) pra monitorar menção de termo/nome ao longo do
  tempo, grátis, sem prazo. Não dá pra automatizar por aqui — se o
  usuário quiser, oriente ele a criar o alerta direto no site (poucos
  cliques, explicar o processo se for a primeira vez).
- **Apify** (não instalado — exige conta) — marketplace de scrapers
  prontos ("Actors"), free tier de $5/mês recorrente em créditos, sem
  cartão. Pra usar: usuário cria conta em `apify.com`, pega o API token
  no painel, aí dá pra chamar os Actors via `curl` normal
  (`https://api.apify.com/v2/...`). Ainda não configurado.
- **Playwright também serve pra capturar imagem de mapa/Street View sem
  API paga:** abrir a página normal do
  `google.com/maps/search/<endereço>` com `page.goto()`, esperar
  carregar, `page.screenshot(path=...)`, depois ler o PNG com `Read`.
  Não é a Street View Static API (que exige billing) — é a mesma página
  que qualquer usuário acessa de graça, só automatizada. Útil pra
  checar presença física real de um endereço, e o painel "Diretório"
  do próprio Maps mostra outras empresas registradas no mesmo prédio
  (revela endereço de coworking/escritório compartilhado, por exemplo).
- **Playwright** (instalado, `python -c "from playwright.sync_api import
  sync_playwright"` + Chromium baixado e testado) — substitui
  Puppeteer/Selenium na curadoria original: mesma capacidade (navegador
  headless real, executa JavaScript, útil quando `curl_cffi` não
  resolve porque a página só renderiza conteúdo via JS), mas em Python,
  consistente com o resto do ambiente. Uso: `sync_playwright()` →
  `p.chromium.launch()` → `page.goto(url)` → `page.content()`. Scrapy
  ficou de fora de propósito — é framework de orquestração pra crawl em
  massa de muitos alvos, não acrescenta capacidade de busca nova sobre
  o que já existe (curl_cffi + Playwright cobrem fetch de alvo único,
  estático ou com JS); reavaliar só se surgir necessidade real de
  varrer muitos alvos de uma vez.
- **Maltego Community Edition** (app baixado pelo usuário, sem conta/uso
  ainda configurado — é aplicativo desktop
  com interface gráfica, não uma API) — ferramenta de grafo de
  investigação (pessoa↔empresa↔imóvel), free tier de 200 créditos/mês.
  **Diferente das outras:** é o usuário quem usa direto, visualmente —
  não é algo que o pesquisador chama via linha de comando. Cabe a mim
  ajudar a montar/interpretar o grafo, não operar o programa sozinho.
  Instalação: baixar em `maltego.com/downloads`, criar conta grátis
  pra ativar a Community Edition.
