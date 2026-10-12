# Bootcamp QI Tech — projeto base da API

Projeto base do Bootcamp: uma API REST em **Python + FastAPI**, com banco
**PostgreSQL**, rodando em **Docker**.

Você não precisa saber programar para começar. A API e o banco sobem
no **Docker**, então você não instala nem um nem outro na sua máquina.
Os **testes** rodam no seu Python — são dois comandos, e a seção 2
mostra os dois.

---

## 0. O que você precisa ter instalado

São três coisas.

| O quê | Para quê | Como conferir |
|---|---|---|
| **Docker** (com o Docker Desktop no Mac/Windows) | roda a API e o banco | `docker compose version` |
| **Git** | trazer o projeto para o seu computador | `git --version` |
| **Python 3.11 ou mais novo** | rodar os testes (seção 2) | `python3 --version` |

Abra o terminal e rode os três comandos da coluna da direita. Se todos
responderem um número de versão, você está pronto.

> **Por que o Python, se tudo roda no Docker?** Porque os testes rodam
> FORA dele, na sua máquina, contra a API que está de pé no container.
> O ganho é o ciclo: você salva um teste e roda na hora, sem esperar
> imagem nenhuma ser montada. O preço está explicado na seção 2.

> **`docker compose version` deu erro?** Sua instalação do Docker é
> antiga demais (ou o Docker não está ligado). No Mac e no Windows,
> abra o **Docker Desktop** e espere a baleia parar de se mexer. Se o
> comando continuar falhando, reinstale pelo site oficial —
> o `docker compose` (com **espaço**) vem junto desde 2022.

Nada além destes três. Se em algum momento este projeto pedir que você
instale outro PROGRAMA, é um bug do projeto — avise a gente. (As
bibliotecas Python que os testes usam são outra conversa: elas entram
com um `pip install` na seção 2, dentro de uma pasta do próprio
projeto, e somem quando você apaga essa pasta.)

---

## 1. Rodando pela primeira vez

```bash
docker compose up
```

Um comando. Só isso, e não precisa criar nem copiar arquivo nenhum
antes: as configurações já vêm com valor padrão dentro do
`docker-compose.yml`.

O Docker baixa o Python, sobe o banco, cria as tabelas e liga a API. Na
primeira vez demora alguns minutos; depois é quase instantâneo.

São duas coisas de pé, e vale saber o nome de cada uma:

| Serviço | O que é |
|---|---|
| `api` | a API que responde às suas requisições |
| `db` | o banco de dados (PostgreSQL) |

O worker, que paga os funcionários das folhas em lotes, não sobe junto:
ele pagaria as folhas antes de os testes conferirem o meio do caminho.
Para ligá-lo, use `docker compose --profile worker up -d worker`; para
desligar, `docker compose --profile worker stop worker`.

Quando aparecer `Application startup complete`, a API está no ar. Abra
no navegador:

### 👉 http://localhost:3000

Você vai ver isto:

```json
{"service":"bootcamp-api","id":"8"}
```

Pouca coisa, e de propósito: essa rota só diz "estou viva, e eu sou este
serviço". Mas você acabou de fazer uma **requisição HTTP** — a mesma
coisa que o navegador faz ao abrir qualquer site.

### Agora as outras rotas

Elas não abrem no navegador, porque exigem um cabeçalho: o
`INTERNAL-TOKEN`, que é a senha da API (seção 6). Para mandar um
cabeçalho a gente usa o `curl`, um programa de linha de comando que já
vem instalado no Mac, no Linux e no Windows.

**Abra um segundo terminal** — o primeiro está ocupado rodando a API — e
cole um comando de cada vez.

> **No Windows**, use o **Git Bash**: ele veio junto com o Git da seção
> 0. No PowerShell estes comandos não funcionam, porque lá `curl` é o
> apelido de outro programa, com outra sintaxe.

#### 1. Criar uma empresa

```bash
curl -X POST http://localhost:3000/company \
  -H "INTERNAL-TOKEN: default_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Padaria do Joao LTDA",
    "document_number": "11.222.333/0001-81",
    "email": "financeiro@padaria.com.br",
    "payment_day": 5,
    "fee_amount": 150
  }'
```

```json
{"company_key":"063a4e0e-bd1d-4bd7-9519-c541a6ef3533"}
```

Esse `company_key` é o endereço da empresa que você acabou de criar.
**Copie o seu** — ele nasce diferente a cada vez, e nos comandos abaixo
você troca o que está escrito aqui pelo seu.

O `fee_amount` é a taxa que a empresa paga por transferência, em
**centavos**: `150` são R$ 1,50. Todo dinheiro nesta API anda em
centavos inteiros, nunca em número quebrado.

> **Rodou o comando duas vezes e levou 409 na segunda?** É de propósito:
> o CNPJ e o e-mail não podem se repetir. Para criar uma segunda
> empresa, troque o e-mail (qualquer um serve) e o CNPJ — mas o CNPJ tem
> que ser **válido de verdade**, com os dois dígitos finais batendo com
> a conta. O `11.222.333/0001-81` acima é um CNPJ de teste conhecido,
> que passa na conta e não pertence a ninguém.
>
> **E os cinco campos são todos obrigatórios?** São. Mande `{}` e a API
> diz qual está faltando — é o comando 6 lá embaixo.

#### 2. Buscar a empresa

```bash
curl http://localhost:3000/company/063a4e0e-bd1d-4bd7-9519-c541a6ef3533 \
  -H "INTERNAL-TOKEN: default_token"
```

```json
{"company_key":"063a4e0e-bd1d-4bd7-9519-c541a6ef3533","name":"Padaria do Joao LTDA","document_number":"11.222.333/0001-81","email":"financeiro@padaria.com.br","payment_day":5,"fee_amount":150}
```

Voltaram os cinco campos que você mandou, mais o `company_key`. O que
**não** voltou também é de propósito: o `id` interno do banco nunca sai
da API. Quem está do lado de fora fala com a empresa pela chave.

#### 3. Listar as empresas

```bash
curl http://localhost:3000/companies \
  -H "INTERNAL-TOKEN: default_token"
```

```json
{"data":[{"company_key":"063a4e0e-bd1d-4bd7-9519-c541a6ef3533","name":"Padaria do Joao LTDA","document_number":"11.222.333/0001-81","email":"financeiro@padaria.com.br","payment_day":5,"fee_amount":150}],"limit":10,"page":0,"is_last_page":true}
```

Vêm de dez em dez, da mais nova para a mais antiga. Para pedir outra
quantidade ou outra página, acrescente `?limit=2&page=0` ao endereço —
o `limit` vai até **100**. O `is_last_page` já responde a pergunta
seguinte — "tem mais?" — sem custar uma segunda requisição.

Também dá para **filtrar pelo nome**, que casa por **pedaço** e
ignorando maiúscula/minúscula — quem procura uma empresa lembra meio
nome:

```bash
curl "http://localhost:3000/companies?name=padaria" \
  -H "INTERNAL-TOKEN: default_token"
```

#### 4. Abrir a conta e colocar dinheiro

Toda empresa tem uma conta, e é dela que sai o dinheiro das
transferências e da folha. Abra a da sua empresa:

```bash
curl -X POST http://localhost:3000/company/063a4e0e-bd1d-4bd7-9519-c541a6ef3533/account \
  -H "INTERNAL-TOKEN: default_token"
```

```json
{"account_key":"0e2c7031-94d1-4655-9046-9ea08fe4793c"}
```

A conta nasce com saldo zero. Nesta entrega o dinheiro só entra no
sistema por uma **rota de teste**, que credita direto, sem taxa. Copie o
seu `account_key` e coloque R$ 1.000,00 (`100000` centavos):

```bash
curl -X POST http://localhost:3000/test/account/0e2c7031-94d1-4655-9046-9ea08fe4793c/credit \
  -H "INTERNAL-TOKEN: default_token" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100000}'
```

```json
{"account_key":"0e2c7031-94d1-4655-9046-9ea08fe4793c","balance_amount":100000}
```

#### 5. Mudar o status da conta

Bloqueie a conta e depois reative:

```bash
curl -X PUT http://localhost:3000/account/0e2c7031-94d1-4655-9046-9ea08fe4793c \
  -H "INTERNAL-TOKEN: default_token" \
  -H "Content-Type: application/json" \
  -d '{"status": "blocked"}'

curl -X PUT http://localhost:3000/account/0e2c7031-94d1-4655-9046-9ea08fe4793c \
  -H "INTERNAL-TOKEN: default_token" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

Cada um responde `{"account_key": ...}`. Agora abra a conta:

```bash
curl http://localhost:3000/account/0e2c7031-94d1-4655-9046-9ea08fe4793c \
  -H "INTERNAL-TOKEN: default_token"
```

```json
{"account_key":"0e2c7031-94d1-4655-9046-9ea08fe4793c","account_type":"company","company_key":"063a4e0e-bd1d-4bd7-9519-c541a6ef3533","employee_key":null,"balance_amount":100000,"status":"active","status_events":[{"status":"active","event_datetime":"2026-10-12T06:10:09.104324"},{"status":"blocked","event_datetime":"2026-10-12T06:10:09.164245"},{"status":"active","event_datetime":"2026-10-12T06:10:09.180016"}]}
```

O `status` diz onde a conta está; o `status_events` diz **por onde ela
passou**. Cada mudança deixou uma linha, com a hora. São duas perguntas
diferentes, e é essa lista que responde a segunda.

Agora tente encerrar a conta:

```bash
curl -X PUT http://localhost:3000/account/0e2c7031-94d1-4655-9046-9ea08fe4793c \
  -H "INTERNAL-TOKEN: default_token" \
  -H "Content-Type: application/json" \
  -d '{"status": "closed"}'
```

```json
{"title":"Account still has balance","description":"Account with key 0e2c7031-94d1-4655-9046-9ea08fe4793c still has a balance of 100000 and cannot be closed.","translation":"A conta ainda tem saldo e não pode ser encerrada.","code":"QIT001023"}
```

Isso é uma **regra de negócio**, não um erro de digitação: encerrar uma
conta com dinheiro dentro faria esse dinheiro sumir. A frase que decide
isso mora em `src/controllers/account_controller.py`, e você pode ir
ler.

#### 6. Mandar um JSON torto

```bash
curl -X POST http://localhost:3000/company \
  -H "INTERNAL-TOKEN: default_token" \
  -H "Content-Type: application/json" \
  -d '{}'
```

```json
{"title":"Bad Request","description":"'name' is a required property","translation":"Payload Inválido","code":"QIT000001"}
```

**400**, e nada foi criado. O `name` é obrigatório, e quem recusou não
foi a regra de negócio: foi o `src/schemas/`, antes da primeira linha da
rota rodar. Pedido torto não chega a custar uma consulta ao banco.

Repare que ele reclamou de **um** campo, e você deixou cinco de fora. É
assim mesmo: a validação para no primeiro problema. Tire o `{}` e vá
preenchendo um campo de cada vez para ver a reclamação andar.

E existe uma fronteira aqui que vale a pena enxergar cedo. Mande um CNPJ
com o formato certo e os dígitos errados:

```bash
curl -X POST http://localhost:3000/company \
  -H "INTERNAL-TOKEN: default_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Padaria do Joao LTDA",
    "document_number": "11.111.111/1111-11",
    "email": "outra@padaria.com.br",
    "payment_day": 5,
    "fee_amount": 150
  }'
```

```json
{"title":"Invalid Company Document Number","description":"The document number 11.111.111/1111-11 is not a valid CNPJ.","translation":"O CNPJ informado não é válido.","code":"QIT001008"}
```

Agora é **422**, não 400. A diferença não é capricho: 400 quer dizer
"não consegui ler o seu pedido"; 422 quer dizer "li, entendi, e esse
valor não pode existir". O schema sabe contar pontos, barras e traços —
ele não sabe fazer a conta dos dois últimos dígitos. Quem sabe é o
`src/utils/document_number.py`, e por isso essa recusa vem de dentro,
com código próprio.

#### Esqueceu o `-H "INTERNAL-TOKEN: ..."`?

A API responde **403** e nem chega a olhar o resto:

```json
{"title":"Forbidden","description":"Request must be internal","translation":"Requisição precisa ser interna","code":"QIT000002"}
```

#### Toda resposta vem com um número de protocolo

Repare no `-i` deste comando: ele mostra os **cabeçalhos** da resposta,
não só o corpo.

```bash
curl -i "http://localhost:3000/companies?limit=1" \
  -H "INTERNAL-TOKEN: default_token"
```

```
HTTP/1.1 200 OK
content-type: application/json
x-request-id: 8f3c1e42-1b0d-4f77-9a55-2e4c9d1f0abc
...
```

Esse `x-request-id` é o **número de protocolo** da sua requisição: um
nome único, criado no instante em que ela chegou. Copie o seu e procure
por ele no log:

```bash
docker compose logs api | grep 8f3c1e42
```

```
[INFO] bootcamp-api.middlewares.request_logger [8f3c1e42-...] - ENTROU GET /companies?limit=1
[INFO] bootcamp-api.middlewares.request_logger [8f3c1e42-...] - SAIU 200 GET /companies - 2.9 ms
```

Duas linhas, o mesmo nome nas duas — e nenhuma outra requisição usa esse
nome. Serve para o dia em que alguém disser "deu erro por volta das
14h30": sem o número, você abre o log e encontra mil linhas parecidas, de
mil requisições diferentes, embaralhadas, porque a API atende várias ao
mesmo tempo e o log é um só. Com o número, achar a agulha é um `grep`.

Se quem chamou já mandar um `x-request-id`, a API **respeita o que veio**
e usa o mesmo — é assim que se segue um único pedido atravessando vários
sistemas:

```bash
curl -i "http://localhost:3000/companies?limit=1" \
  -H "INTERNAL-TOKEN: default_token" \
  -H "X-Request-ID: meu-teste-1"
```

Experimente mandar um valor esquisito nesse cabeçalho — com espaços, ou
bem comprido. A API não devolve o que você mandou: ela troca por um novo.
O porquê está em `src/utils/request_context.py`, e é uma das poucas
lições de segurança que cabem em cinco linhas.

> Só o `/` e o `/health_check` não aparecem no log: o Docker consulta o
> health check a cada três segundos, e sem essa exceção o log seria
> quase só isso. Eles ganham o `x-request-id` como todo mundo — o que
> não ganham é a linha de log.

### Todas as rotas

Este é o mapa inteiro da API. O contrato completo de cada rota — os
campos, cada status de resposta e quando ele acontece — está no RFC
(`bootcamp-rfc-modelo.md`, seção "Rotas").

| Método e rota | O que faz | Responde |
|---|---|---|
| `GET /` | diz qual serviço é este | `200` + nome e id |
| `GET /health_check` | diz se a API está de pé | `204`, sem corpo |
| `POST /company` | cria a empresa | `201` + `company_key` |
| `GET /company/{company_key}` | busca a empresa | `200` + a empresa |
| `PUT /company/{company_key}` | altera a taxa (`fee_amount`) | `202` + `company_key` |
| `GET /companies` | lista as empresas | `200` + a página |
| `POST /company/{company_key}/position` | cria um cargo | `201` + `position_key` |
| `GET /company/{company_key}/positions` | lista os cargos da empresa | `200` + a lista |
| `POST /company/{company_key}/employee` | cria o funcionário | `201` + `employee_key` |
| `GET /employee/{employee_key}` | busca o funcionário | `200` + o funcionário |
| `PUT /employee/{employee_key}` | troca o cargo ou desliga | `202` + `employee_key` |
| `GET /company/{company_key}/employees` | lista os funcionários | `200` + a página |
| `POST /company/{company_key}/account` | abre a conta da empresa | `201` + `account_key` |
| `POST /employee/{employee_key}/account` | abre a conta do funcionário | `201` + `account_key` |
| `GET /account/{account_key}` | saldo, status e história da conta | `200` + a conta |
| `PUT /account/{account_key}` | bloqueia, reativa ou encerra | `202` + `account_key` |
| `GET /account/{account_key}/statement` | extrato da conta | `200` + a página |
| `POST /test/account/{account_key}/credit` | **teste:** coloca dinheiro, sem taxa | `201` + o saldo |
| `POST /transfer` | transfere entre contas, com taxa | `201` + `transfer_key` |
| `POST /transfer/external` | **simula** transferência para outro banco | `201` + `transfer_key` |
| `GET /transfer/{transfer_key}` | busca a transferência | `200` + a transferência |
| `POST /company/{company_key}/payroll` | gera a folha do mês | `201` + a folha |
| `GET /payroll/{payroll_key}` | busca a folha, com os itens | `200` + a folha |
| `GET /company/{company_key}/payrolls` | lista as folhas da empresa | `200` + a página |
| `PUT /payroll/{payroll_key}/pay` | começa o pagamento | `202` + `payroll_key` |
| `PUT /payroll/{payroll_key}/retry` | devolve para a fila os itens que falharam | `202` + `payroll_key` |
| `PUT /payroll/{payroll_key}/refund` | devolve à empresa o dinheiro dos itens que falharam | `202` + `payroll_key` |
| `PUT /payroll/{payroll_key}/cancel` | cancela a folha antes do pagamento | `202` + `payroll_key` |
| `POST /test/payroll/{payroll_key}/process` | **teste:** roda o worker na hora para a folha | `200` + o status |

Todas exigem o `INTERNAL-TOKEN` (seção 6), menos as duas de cima — a
primeira você já usou: foi ela que respondeu no navegador. O
`/health_check` responde `204`, que quer dizer "deu certo e não tenho
nada a dizer"; use `curl -i` para ver o status, já que não vem corpo.

As listagens que devolvem página aceitam `?limit=` (padrão 10, teto
100) e `?page=` (padrão 0), mais os filtros de cada uma: `?name=` nas
empresas; `?name=` e `?active=` nos funcionários; `?date_from=` e
`?date_to=` no extrato; `?status=` nas folhas. Qualquer outro nome a
API **recusa** com 400 — é o schema da rota, em `src/schemas/`, que
decide, e ele não aceita o que não conhece. Vale a pena errar de
propósito uma vez:

```bash
curl "http://localhost:3000/companies?nmae=padaria" \
  -H "INTERNAL-TOKEN: default_token"
```

```json
{"title":"Bad Request","description":"Additional properties are not allowed ('nmae' was unexpected)","translation":"Payload Inválido","code":"QIT000001"}
```

Sem essa recusa, um `nmae` com as letras trocadas viraria uma lista
inteira devolvida como se o filtro tivesse funcionado — o pior tipo de
bug, o que não reclama.

Para desligar tudo: `Ctrl+C` no terminal da API e depois

```bash
docker compose down
```

---

## 2. Rodando os testes

Os testes rodam **na sua máquina**, contra a API que está de pé no
Docker. Então são dois passos: um de uma vez só, outro toda vez.

**Uma vez só — instalar as dependências de teste:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

O `.venv` é uma pasta com um Python só deste projeto. Ele existe pra que
instalar algo aqui não mexa no Python da sua máquina — e pra que apagar a
pasta desfaça tudo. No Windows, a segunda linha é
`.venv\Scripts\activate`.

**Toda vez — com a API de pé, em outro terminal:**

```bash
pytest
```

A API precisa estar respondendo antes. Se você acabou de dar
`docker compose up`, espere o `(healthy)` aparecer — é o healthcheck do
`docker-compose.yml` dizendo que a porta já atende. Sem isso, o primeiro
teste bate numa porta que ainda não responde.

O resultado sai assim:

```
tests/integration/test_healthcheck.py::TestHealthCheck::test_home PASSED
...
============================== 35 passed in 1.54s ==============================
```

Para rodar só um arquivo (ou só um teste), acrescente o caminho:

```bash
pytest -v tests/integration/test_healthcheck.py
```

Os testes leem o seu `.env` sozinhos (é o `tests/conftest.py` que faz
isso). Trocou a porta da API ali, os testes passam a bater na porta nova
— você não configura a mesma coisa em dois lugares.

Os testes conversam com a API **por HTTP**, exatamente como um cliente de
verdade faria. Eles não espiam o código por dentro: nenhum deles importa
nada de `src/`. Só sabem: "mandei isso, tem que voltar aquilo".

> Uma exceção, e ela é honesta: `tests/utils/db_utils.py` fala com o
> banco direto, por SQLAlchemy. Mas não para **montar** cenário — só
> para **zerar** o banco entre testes que não podem se atrapalhar. O
> cenário continua nascendo pela API, com `POST`.

Isso tem uma consequência bonita: **este projeto inteiro já foi reescrito
de um framework para outro, e nenhum teste precisou mudar.** Quando o
teste descreve o combinado em vez de descrever o código, ele sobrevive à
reforma.

## 3. Quando dá errado

Os tropeços mais comuns, com a mensagem que você vai ver:

### `port is already allocated`

```
Bind for 0.0.0.0:5432 failed: port is already allocated
```

Outro programa da sua máquina já usa aquela porta (é comum ter um
Postgres instalado ocupando a 5432). Não precisa descobrir qual: escolha
outras portas livres. É pra isto que serve o `.env` —

```bash
cp .env.example .env
```

— e, dentro dele, tire o `#` da frente destas duas linhas e troque os
números:

```
API_PORT=3001
DB_PORT=5433
```

Mexeu no `DB_PORT`? Então mude **também** a porta da `DATABASE_URL`, no
mesmo arquivo:

```
DATABASE_URL=postgresql+psycopg2://bootcamp:bootcamp@localhost:5433/bootcamp
```

São dois lugares porque são dois pontos de vista. O `DB_PORT` diz em
que porta **da sua máquina** o banco aparece; a `DATABASE_URL` é o
endereço que os testes usam para chegar nele de fora do Docker. A API
lá dentro não usa nenhuma das duas — para ela o banco é `db:5432`, e
por isso essa linha está fixa no `docker-compose.yml`.

Suba de novo. Agora a API atende em http://localhost:3001 — e nos
comandos `curl` da seção 1 você troca `3000` por `3001`.

### `failed to connect to the docker API`

```
failed to connect to the docker API at unix:///var/run/docker.sock;
check if the path is correct and if the daemon is running
```

O Docker não está ligado. Abra o **Docker Desktop** (Mac/Windows) e
espere ficar verde. No Linux: `sudo systemctl start docker`.

### `Não consegui falar com a API` / `Não consegui falar com o banco`

Só aparece no atalho local (fora do Docker). Quer dizer que a API ou o
banco não estão de pé, ou que a porta no seu `.env` não é a que eles
estão usando. Suba com `docker compose up` e confira as portas.

### `relation "..." does not exist`

```
psycopg2.errors.UndefinedTable: relation "minha_tabela" does not exist
```

Você mexeu no `database/database.sql`, e o banco não ficou sabendo.
Aquele arquivo roda **uma vez só: quando o banco nasce.** Depois disso o
Postgres nunca mais olha para ele — subir de novo com `docker compose
up` não adianta, e `docker compose restart db` também não.

Repare no que a mensagem faz com você: ela não diz "seu SQL não rodou",
diz que a tabela não existe. Você vai reler o seu SQL procurando um erro
de digitação que não está lá.

Para o banco nascer de novo, já com o schema novo:

```bash
docker compose down -v
docker compose up
```

O `-v` é o que apaga o volume — o disco do banco. **Ele leva junto tudo
que você tinha criado na mão**, a empresa e a conta dos `curl` da seção 1. Não
tem meio-termo: ou o banco nasce de novo com o schema novo, ou continua
com o antigo. (Em sistema de verdade é outra história — lá ninguém apaga
o banco, e a mudança de schema entra por um comando aplicado no deploy.)

### Nada disso resolveu?

Este comando desliga e limpa **este** projeto (containers, rede e o
banco com tudo dentro) para você recomeçar do zero:

```bash
docker compose down -v
docker compose up
```

Para ver o que a API está dizendo enquanto roda: `docker compose logs -f api`.

---

## 4. As pastas

```
src/
  app.py           ← liga tudo: rotas, middlewares e tratamento de erro
  database.py      ← onde a sessão de banco mora (quem cuida do ciclo
                     dela é middlewares/session_manager.py)
  constants.py     ← as configurações, lidas do ambiente

  resources/       ← recebe a requisição HTTP e devolve a resposta
                     (quem liga cada endereço a um resource é o app.py)
  schemas/         ← o formato do que entra: o JSON do corpo e os
                     parâmetros do endereço
  controllers/     ← as regras de negócio: o que pode e o que não pode
  repositories/    ← as conversas com o banco
  models/          ← as tabelas, descritas em Python
  dtos/            ← traduz o objeto do banco no JSON que sai
  errors/          ← os erros da API, cada um com seu código
  middlewares/     ← o que acontece com TODA requisição
  connectors/      ← as conversas com outros serviços
  utils/           ← as ferramentas que não são de nenhuma camada

database/
  database.sql     ← as tabelas, em SQL puro

tests/             ← os testes
```

### Por que tanta pasta?

Porque cada uma tem **um trabalho só**, e só conversa com a vizinha:

```
requisição → resource → controller → repository → banco
                 ↑           ↑
             valida o     decide o
              formato     que pode
```

O resource não sabe SQL. O repository não sabe o que é uma regra de
negócio. Um teste rápido para saber se uma linha está na pasta certa:
**nenhum `raise` mora em `resources/`** — quem recusa é o schema, antes,
ou o controller, depois. Confira você mesmo:

```bash
grep -rn "raise" src/resources/
```

Não volta nada, e isso é de propósito. Quando você precisa trocar o banco, mexe numa pasta. Quando a
regra muda, mexe na outra. É isso que permite um time inteiro trabalhar
no mesmo projeto sem pisar no pé um do outro.

---

## 5. Configuração e senhas

Toda configuração entra por **variável de ambiente** — nunca escrita no
meio do código.

- **valor padrão** → escrito no `docker-compose.yml`, na forma
  `${VARIAVEL:-padrao}`. É por causa dele que o `docker compose up`
  funciona sem preparo nenhum.
- `.env` → **opcional**, fica só na sua máquina e **nunca** vai para o
  Git. Serve para sobrescrever um padrão (porta ocupada, outro token).
- `.env.example` → vai para o Git, e é a cópia de onde você parte. Só
  tem valor de mentirinha.

Essa separação não é frescura. Senha commitada em repositório é uma das
formas mais comuns de vazamento de dados no mundo real, e não tem
desfazer: uma vez no histórico, está lá para sempre.

Uma ressalva honesta: valor padrão de senha em arquivo versionado só
vale porque aqui é um projeto de estudo, sem dado de ninguém. Em
sistema de verdade, segredo não tem padrão — ele falta, e a aplicação
se recusa a subir sem ele.

## 6. Autenticação

As rotas de negócio pedem um cabeçalho:

```
INTERNAL-TOKEN: default_token
```

Sem ele, a API responde **403**. `default_token` é o valor padrão; para
trocar, ponha `INTERNAL_TOKEN=outra_coisa` no seu `.env`.

Ficam abertas, de propósito, só duas: a rota raiz e o `/health_check`
— esta última porque quem a consulta é o próprio Docker, que não tem
como mandar cabeçalho.

---

## 7. Os códigos de erro

Todo erro da API responde no mesmo formato, com um código próprio:

```json
{
  "title": "Bad Request",
  "description": "'name' is a required property",
  "translation": "Payload Inválido",
  "code": "QIT000001"
}
```

| Código      | Quando acontece                                  |
|-------------|--------------------------------------------------|
| `QIT000001` | o JSON enviado está fora do formato              |
| `QIT000002` | faltou o `INTERNAL-TOKEN`, ou ele está errado    |
| `QIT000010` | os parâmetros do endereço se contradizem         |
| `QIT000404` | essa rota não existe                             |
| `QIT000405` | a rota existe, mas não aceita esse método        |
| `QIT000500` | erro inesperado (o time é avisado)               |
| `QIT001003` | o CPF tem o formato certo, mas não é um CPF      |
| `QIT001008` | o CNPJ tem o formato certo, mas não é um CNPJ    |
| `QIT001009` | já existe uma empresa com esse CNPJ              |
| `QIT001010` | já existe uma empresa com esse e-mail            |
| `QIT001011` | a empresa procurada não existe                   |
| `QIT001012` | a empresa já tem um cargo com esse nome          |
| `QIT001013` | o cargo não existe nessa empresa                 |
| `QIT001014` | a empresa já tem um funcionário com esse CPF     |
| `QIT001015` | a data não existe no calendário                  |
| `QIT001016` | o funcionário procurado não existe               |
| `QIT001017` | o funcionário já foi desligado                   |
| `QIT001018` | o desligamento é anterior à contratação          |
| `QIT001019` | a empresa já tem conta                           |
| `QIT001020` | o funcionário já tem conta                       |
| `QIT001021` | a conta procurada não existe                     |
| `QIT001022` | a conta está encerrada                           |
| `QIT001023` | a conta ainda tem saldo e não pode ser encerrada |
| `QIT001024` | a conta não está ativa                           |
| `QIT001025` | a transferência procurada não existe             |
| `QIT001026` | a origem e o destino são a mesma conta           |
| `QIT001027` | a conta do banco não pode ser destino            |
| `QIT001028` | o saldo não cobre o valor mais a taxa            |
| `QIT001029` | a chave de idempotência já foi usada em outro pedido |
| `QIT001030` | a folha procurada não existe                     |
| `QIT001031` | a empresa já tem folha não cancelada nesse mês   |
| `QIT001032` | a empresa não tem funcionário ativo              |
| `QIT001033` | há funcionário ativo sem conta ativa             |
| `QIT001034` | a API de cálculo não respondeu, demorou ou deu erro |
| `QIT001035` | a API de cálculo respondeu um valor inválido     |
| `QIT001036` | a folha não está `pending`                       |
| `QIT001037` | a folha não está `processing`                    |
| `QIT001038` | a folha não tem item que falhou                  |
| `QIT001039` | a conta de liquidação não entra em transferência |
| `QIT001040` | a empresa não tem conta para pagar a folha       |

Um código estável vale mais que uma mensagem bonita: quem integra com a
API programa em cima do código, não do texto.

Os números não são sorteados. Eles vêm em duas faixas:

- **`QIT000…`** — os erros que **toda** API tem: JSON errado, sem token,
  rota inexistente. Estão em `src/errors/base_error.py` e você não
  precisa mexer neles.
- **`QIT001…`** — os erros das **regras deste projeto**. Estão em
  `src/errors/custom_errors.py`, e é aí que os seus entram: o próximo
  livre é o `QIT001041`.

Não repita um número. Se repetir, a API **não sobe** — tem uma checagem
no start (`error_verification`, em `src/errors/base_error.py`) que
procura código repetido e derruba a aplicação de propósito. Parecer
chato agora é melhor que dois erros diferentes chegarem ao cliente com o
mesmo código.

Os buracos na tabela (`QIT001001`, `QIT001002` e de `QIT001004` a
`QIT001007`) também são de propósito: eram de uma entidade de exemplo que
saiu do projeto. Código aposentado não volta a ser usado — um cliente
antigo ainda pode tratar aquele número com o significado velho.

---

## 8. A licença

Este projeto é **MIT** — pode usar, copiar, modificar e levar para o seu
portfólio, inclusive em trabalho pago. O único pedido é manter o arquivo
`LICENSE` junto quando você distribuir o código.
