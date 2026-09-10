# Comentários de rede social

Quando a unidade atômica pedir avaliar **reação/opinião real de usuário**
em comentário (não só o conteúdo do post/vídeo em si) — validar
recepção de um produto/vídeo, sentimento do público, reclamação
recorrente:

- **YouTube** — API oficial, gratuita, chave própria configurada
  (`YOUTUBE_API_KEY` no `.env`), cota de 10.000 unidades/dia (1 por
  chamada — folgado pra uso esporádico):
  ```
  curl "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId=<ID_DO_VIDEO>&maxResults=20&key=$YOUTUBE_API_KEY"
  ```
  `videoId` é o trecho depois de `v=` na URL do vídeo. Cada item vem em
  `items[].snippet.topLevelComment.snippet` (`textDisplay`,
  `authorDisplayName`, `likeCount`, `publishedAt`). Tratar como sinal
  de opinião real, mesma regra de triangulação do Passo 2 — não vira
  "confirmado" sozinho, mas é exatamente o tipo de fonte que revela
  reclamação/elogio que a doc oficial do produto não menciona.

- **Instagram e X (Twitter)** — sem API oficial acessível pra ler
  comentário de conta de terceiro (a API oficial de ambos só cobre
  conta própria do usuário autenticado). Caminho viável: **Apify**
  (token próprio em `APIFY_API_TOKEN` no `.env`), via os Actors
  `Instagram Comments Scraper` e `Twitter (X) Comment Scraper` —
  scraping não-oficial, **viola os Termos de Uso das duas plataformas**
  (mesma categoria de risco já sinalizada pro Sherlock — funciona
  tecnicamente, é contra a regra deles). **Só usar quando o usuário
  pedir explicitamente pra essa rede especificamente** — Instagram/X
  não entram por padrão numa busca geral, mesmo que a unidade atômica
  fizesse sentido pra eles, por questão de responsabilidade (decisão
  explícita do usuário). Sempre mencionar isso junto do resultado,
  nunca esconder. **Estado real: configurado, NÃO validado com
  extração de verdade** — token e existência dos Actors confirmados,
  mas nunca rodado `run-sync-get-dataset-items` de fato (rodar é usar
  a ferramenta, reservado pra "só sob pedido"). Primeira vez que for
  usado numa busca real, tratar como primeira validação do schema de
  saída. Uso via `curl` na API REST da Apify (IDs de Actor reais,
  confirmar antes de usar que ainda existem/mudaram de nome):
  ```
  # Instagram (Actor automation-lab/instagram-comments-scraper)
  curl -X POST "https://api.apify.com/v2/acts/automation-lab~instagram-comments-scraper/run-sync-get-dataset-items?token=$APIFY_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"directUrls": ["<url_do_post>"], "resultsLimit": 50}'

  # X/Twitter (Actor muhammetakkurtt/twitter-x-comment-scraper)
  curl -X POST "https://api.apify.com/v2/acts/muhammetakkurtt~twitter-x-comment-scraper/run-sync-get-dataset-items?token=$APIFY_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"directUrls": ["<url_do_post>"], "resultsLimit": 50}'
  ```
  Cada Actor pode ter campos de input específicos além de `directUrls`
  (checar a doc do Actor na Apify se o resultado vier vazio/incompleto —
  schema de input pode mudar por versão). Crédito gratuito da Apify é
  $5/mês — curto pra scraping em volume (Instagram
  ~$0,0023/comentário, uns 2.000 comentários grátis por mês somando
  todas as chamadas) — avisar o usuário se uma busca específica for
  consumir uma fatia grande do crédito do mês.
