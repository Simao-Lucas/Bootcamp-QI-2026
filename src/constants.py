import os


SERVICE_ROOT = os.path.abspath(os.path.dirname(__file__))

# Onde moram os arquivos de schema — os .json que descrevem o formato
# que cada requisicao precisa ter. Quem le essa pasta e o
# src/utils/schema_handler.py.
SCHEMA_PATH = os.path.join(SERVICE_ROOT, "schemas")

APP_ENV = os.environ.get("APP_ENV", "local")
SERVICE_NAME = os.environ.get("SERVICE_NAME", "bootcamp-api")

DATABASE_URL = os.environ.get("DATABASE_URL")
INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN")

# A API de boletos: o serviço de fora que este projeto chama pra emitir
# uma cobrança (veja src/connectors/). O endereço vem do ambiente, como
# tudo aqui — na sua máquina ele aponta pro mock server do sábado 4; em
# produção, apontaria pro serviço de verdade. O código não sabe a
# diferença, e esse é o ponto.
BANKSLIP_API_URL = os.environ.get("BANKSLIP_API_URL", "http://localhost:8080")
BANKSLIP_API_INTERNAL_TOKEN = os.environ.get("BANKSLIP_API_INTERNAL_TOKEN", "default_token")

# Quantos segundos esperar pelo serviço de boletos antes de desistir.
# Todo connector TEM um timeout — o porquê está em
# src/connectors/rest_connector.py.
BANKSLIP_API_TIMEOUT = int(os.environ.get("BANKSLIP_API_TIMEOUT", "5"))

# A API de cálculo de salários: devolve quanto cada funcionário recebe
# de verdade, na criação da folha. O contrato está na seção "API externa
# de cálculo" do RFC. No docker compose, quem responde é o MockServer.
CALCULATION_API_URL = os.environ.get("CALCULATION_API_URL", "http://localhost:1080")
CALCULATION_API_INTERNAL_TOKEN = os.environ.get("CALCULATION_API_INTERNAL_TOKEN", "default_token")
CALCULATION_API_TIMEOUT = int(os.environ.get("CALCULATION_API_TIMEOUT", "5"))

# O worker da folha (src/worker.py): quantos itens cada lote paga, numa
# transação só, e quantos segundos ele espera quando não acha nada para
# pagar. Lote maior trava mais contas por mais tempo; menor faz mais commits.
PAYROLL_BATCH_SIZE = int(os.environ.get("PAYROLL_BATCH_SIZE", "500"))
WORKER_INTERVAL_SECONDS = float(os.environ.get("WORKER_INTERVAL_SECONDS", "5"))

# Rotas públicas: não exigem o header INTERNAL-TOKEN. São as duas que
# precisam responder pra quem ainda não tem token nenhum: a raiz, que
# diz quem é este serviço, e o health check, que o Docker consulta pra
# saber se a API já está de pé.
BYPASS_ENDPOINTS = [
    "/",
    "/health_check",
]

REQUIRED_VARIABLES = ["DATABASE_URL", "INTERNAL_TOKEN"]

# O worker não atende requisição nenhuma, então não confere token.
WORKER_REQUIRED_VARIABLES = ["DATABASE_URL"]


def check_variables(required_variables: list = None):
    if required_variables is None:
        required_variables = REQUIRED_VARIABLES

    missing = []
    for name in required_variables:
        if not globals().get(name):
            missing.append(name)

    if missing:
        raise EnvironmentError(
            f"Faltam variáveis de ambiente: {', '.join(missing)}. "
            "Rodando com 'docker compose up' elas já vêm preenchidas. "
            "Fora do Docker, copie o .env.example para .env."
        )
