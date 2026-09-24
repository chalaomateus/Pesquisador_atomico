# Investigação visual (foto/screenshot)

Quando a unidade atômica pedir informação extraída de uma IMAGEM (não
texto) — local, data, pessoas visíveis, se a imagem é autêntica, onde
mais ela circula na web — siga este processo. Não é o caso comum, só
ativa quando o despacho trouxer um caminho de arquivo de imagem.

Este arquivo resume, pro fluxo do Pesquisador, a mesma sequência que
`~/.claude/skills/where-was-this-taken/SKILL.md` já define como método
completo e testado (metadado → procedência → geolocalização →
cronolocalização → autenticidade), com grau de confiança formal
(Confirmado/Provável/Região só/Excluído/Não resolvido) e teste de
falsificação explícito — consulte ela direto se a unidade atômica
pedir o processo completo, não só um dos passos isolados. O que este
arquivo acrescenta e que a skill mestre não cobre: o limite legal
específico pra investigação de crédito (Passo 5) e a regra de escopo
pra caso real de investigação de crédito (final do arquivo).

## Pré-requisito

A imagem precisa estar salva em arquivo local, com o caminho absoluto
informado no próprio despacho. Você não recebe imagem anexada direto
no chat como o Claude-orquestrador recebe — se o despacho não trouxer
um caminho de arquivo, avise que precisa dele antes de continuar (não
invente conteúdo de imagem que não foi de fato aberta com `Read`).

**Escopo travado no que veio no despacho:** o processo abaixo vale só
pra imagem específica que o despacho apontou (o print que o usuário já
via de forma legítima). Nunca vira licença pra ir buscar mais fotos do
mesmo perfil, dos marcados ou dos amigos — isso é uma decisão nova,
não uma continuação automática deste processo.

## Passo 0 — Metadado (grátis, faça sempre primeiro)

Antes de qualquer inventário visual, rode `exiftool -G1 -a -u -g1
<caminho>` na imagem ORIGINAL (nunca numa cópia já recortada/editada —
cortar ou girar reescreve os metadados). Método completo, incluindo o
que priorizar (GPS, GPSImgDirection, timestamps, corrente de edição):
`~/.claude/skills/secrets-in-file-metadata/SKILL.md`

Se já vier coordenada GPS no EXIF, trate como pista a confirmar
visualmente no Passo 2, não como resposta pronta — mas pode encurtar
bastante o resto do processo quando a imagem não passou por rede
social (rede social costuma remover o EXIF no reencode; anexo enviado
"como arquivo" no WhatsApp costuma preservar).

## Passo 1 — Inventariar ANTES de buscar

Abra a imagem com `Read` (é multimodal) e liste toda pista visível
antes de pesquisar qualquer coisa — nome de negócio, placa,
idioma/roteiro do texto, poste, sinalização, arquitetura, vegetação,
nessa ordem de força (pista tier 1 vale mais que vinte pistas tier 6).
Método completo, com a tabela de tiers:
`~/.claude/skills/geolocate-from-pixels/SKILL.md`

## Passo 2 — Local e data (se a unidade pedir)

Siga o método de 8 passos dessa mesma skill (fixar país → ler o texto
de verdade → narrar localidade → consultar geometria via Overpass →
confirmar em imagem de satélite/rua → cronolocalizar por sombra/estação
→ score com 3 pistas independentes batendo). Grade de confiança própria
da skill (Confirmado / Provável / Região só / Não confirmado /
Excluído) — usar essa escala, não inventar outra.

**Geolocalizar a residência de um terceiro não identificado (não o
investigado) exige a mesma autorização explícita do Passo 5 antes de
rodar** — uma foto tirada na casa de alguém, mesmo sem nome, mais uma
descrição, já entrega o endereço da pessoa. Isso é identificação por
associação, não por nome, e tem o mesmo risco.

## Passo 3 — Autenticidade (se houver dúvida sobre a imagem ser real)

Consulte `~/.claude/skills/is-this-photo-real/SKILL.md` e
`reference/verification-checklist.md` — sinais de manipulação, imagem
gerada por IA, artefato de compressão, inconsistência de luz/sombra.
Vale rodar antes de confiar em qualquer achado dos Passos 1-2 e 4-5
quando a origem da imagem for incerta (print repassado, sem saber quem
tirou).

## Passo 4 — Origem / onde mais essa imagem circula (busca reversa)

**Exige autorização explícita do usuário/orquestrador antes de rodar,
sempre que a imagem for de caso real** — não é passo automático. A
razão: os motores exigem subir o arquivo pra infraestrutura de
terceiro (Yandex é empresa russa; via Browserbase, passa ainda por um
segundo terceiro). Isso é enviar dado pessoal do investigado, e possivelmente
de terceiros, pra fora do controle direto — mesma lógica do art. 33 da
LGPD (transferência internacional de dado).

Quando autorizado, siga `~/.claude/skills/find-the-original-image/SKILL.md`:
Google Lens (objeto, texto, marco), Bing Visual Search (recorte de
região específica), TinEye (ordenar por mais antiga, achar cópia
modificada).

**Nunca recorte e busque o ROSTO de uma pessoa não identificada, em
nenhum motor — incluindo Yandex.** O Yandex faz correspondência por
similaridade facial (mesma família de capacidade do PimEyes/FaceCheck.ID
citados no Passo 5, só que embutida num motor de busca reversa comum) —
buscar rosto de desconhecido nele é reconhecimento facial na prática,
mesmo sem passar por uma ferramenta com esse nome no rótulo. Rosto de
pessoa já identificada por outra fonte do caso (ver Passo 5) também não
entra em motor nenhum — a busca reversa serve pra achar ONDE a imagem
circula (objeto, cena, texto), não pra confirmar identidade de rosto.

**Limite técnico ainda não validado:** esses motores pedem upload de
arquivo — `WebFetch` não faz upload, só `Browserbase` (`act`) poderia
simular isso, e nunca foi testado de verdade nesta configuração. Até a
primeira tentativa real, tratar como "configurado, não validado" (mesmo
padrão já usado pro Instagram/X via Apify).

## Passo 5 — Pessoas visíveis na imagem (limite legal explícito)

**Menor de idade visível na foto: registre só "menor presente", sem
descrição, sem recorte, sem busca — mesmo se a criança já foi nomeada
em outro documento do caso.** Sem exceção (LGPD art. 14, melhor
interesse da criança).

Pra adulto, descreva só o que tem relevância pro vínculo patrimonial da
investigação — ex. "adulto ao lado do investigado, segurando chave de
veículo" — não um perfil físico/demográfico completo. **Nunca infira ou
registre raça/etnia, condição de saúde, religião ou orientação sexual
de ninguém na imagem** — são categorias de dado sensível (LGPD art. 5º,
II), e a foto já contém a informação sem precisar da sua inferência
verbalizada sobre ela.

**Nunca rode reconhecimento facial ou busca biométrica (PimEyes,
FaceCheck.ID, Yandex por rosto, ou equivalente) para tentar descobrir o
nome de uma pessoa desconhecida na foto.** Dado biométrico é categoria
especial de dado sensível (GDPR Art. 9, mesma lógica pra LGPD), e essas
ferramentas proíbem nos próprios termos rodar contra rosto de terceiro
sem consentimento dele.

**A identificação de quem aparece na foto só pode vir do contexto que a
própria publicação já expõe** — dono do perfil, marcação de nome, legenda
— nunca de você comparando o rosto com outra foto do investigado pra
"confirmar" que é a mesma pessoa. Comparar rosto pra confirmar identidade
é a mesma operação que reconhecimento facial, só que feita à mão; se o
despacho pedir isso, recuse e explique por quê.

**Ter sido citado em algum lugar do caso não torna a pessoa alvo
legítimo de descrição.** A base legal aqui é proteção ao crédito (LGPD
art. 7º, X), que cobre o investigado e quem tiver relevância patrimonial
real no caso (ex. sócio, possível laranja com vínculo documentado) — não
qualquer pessoa que apareça do lado numa foto. Terceiro sem esse vínculo
já estabelecido: registre como "pessoa não identificada, sem tentativa
de identificação" e pare aí. Não é o Pesquisador quem decide se vale
escalar — essa decisão é do usuário/orquestrador, caso a caso, com base
jurídica explícita, nunca automática.

## Confidencialidade (caso real de investigação)

Se a imagem for de um caso real (ex. investigação patrimonial de
crédito), a descrição do caso nunca vai pro vault pessoal nem pro
repositório público do Pesquisador — mesma regra que já vale pro resto
do agente. Se o achado for bom o suficiente pra guardar, isso é
decisão do usuário, formatada mas não arquivada por você.
