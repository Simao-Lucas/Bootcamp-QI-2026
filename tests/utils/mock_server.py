from os import environ

from requests import put
from requests.exceptions import ConnectionError as RequestsConnectionError


MOCKSERVER_URL = environ.get("MOCKSERVER_URL", "http://localhost:1080")
CALCULATION_PATH = "/salary_calculation"

MOCKSERVER_OFFLINE = (
    "Não consegui falar com o MockServer em {base_url}.\n"
    "Ele faz o papel da API de cálculo e precisa estar de pé. Suba com:  docker compose up\n"
    "Se ele já está de pé em outra porta, ajuste a MOCKSERVER_URL do seu .env."
)


def calculation_timeout() -> int:
    """O timeout que a API usa com a API de cálculo, em segundos.

    O valor vem da mesma variável que o docker-compose repassa ao
    container. Quem testa resposta atrasada precisa atrasar MAIS que isso.
    """
    return int(environ.get("CALCULATION_API_TIMEOUT", "5"))


def calculation_matcher(employee_key: str) -> dict:
    """Casa só as chamadas de cálculo DESTE funcionário.

    O `ONLY_MATCHING_FIELDS` faz o MockServer olhar apenas o
    `employee_key` do corpo. Como cada teste cria os próprios
    funcionários, um teste nunca responde pelo outro, e nenhum precisa
    limpar o MockServer inteiro.
    """
    return {
        "method": "POST",
        "path": CALCULATION_PATH,
        "body": {
            "type": "JSON",
            "json": {"employee_key": employee_key},
            "matchType": "ONLY_MATCHING_FIELDS",
        },
    }


class MockServerUtils:
    """Diz ao MockServer o que a API de cálculo deve responder.

    Funcionário sem expectativa nenhuma recebe 404 do MockServer, que é
    resposta fora do contrato: serve para testar a API de cálculo
    respondendo errado sem configurar nada.
    """

    @staticmethod
    def send(endpoint: str, payload: dict, params: dict = None):
        try:
            response = put(f"{MOCKSERVER_URL}{endpoint}", json=payload, params=params, timeout=10)
        except RequestsConnectionError:
            raise RuntimeError(MOCKSERVER_OFFLINE.format(base_url=MOCKSERVER_URL)) from None

        return response

    @staticmethod
    def reset() -> None:
        """Apaga todas as respostas e chamadas gravadas no MockServer.

        Os testes nunca apagam as próprias respostas, e o MockServer compara
        cada chamada com todas as que guardou: sem esta limpeza no começo de
        cada sessão, ele fica mais lento a cada rodada da suíte, até a
        consulta das chamadas passar do timeout. Com ele fora do ar, não faz
        nada: só os testes da folha precisam dele, e eles avisam sozinhos.
        """
        try:
            put(f"{MOCKSERVER_URL}/mockserver/reset", timeout=10)
        except RequestsConnectionError:
            pass

    @staticmethod
    def expect_calculation(
        employee_key: str, status_code: int = 200, body=None, delay_seconds: int = None
    ) -> None:
        """Uma resposta da API de cálculo para o funcionário.

        `body` dicionário vira JSON; texto vira um corpo que não é JSON.
        A resposta nova substitui a anterior do mesmo funcionário: com
        duas, o MockServer usaria a mais antiga. As chamadas já gravadas
        continuam lá.
        """
        response = MockServerUtils.send(
            "/mockserver/clear", calculation_matcher(employee_key), params={"type": "EXPECTATIONS"}
        )
        assert response.status_code == 200, response.text

        http_response = {"statusCode": status_code}

        if isinstance(body, str):
            http_response["body"] = {"type": "STRING", "string": body}
        elif body is not None:
            http_response["body"] = {"type": "JSON", "json": body}

        if delay_seconds is not None:
            http_response["delay"] = {"timeUnit": "SECONDS", "value": delay_seconds}

        expectation = {
            "httpRequest": calculation_matcher(employee_key),
            "httpResponse": http_response,
        }

        response = MockServerUtils.send("/mockserver/expectation", expectation)
        assert response.status_code == 201, response.text

    @staticmethod
    def expect_net_amount(employee_key: str, net_amount: int) -> None:
        MockServerUtils.expect_calculation(employee_key, body={"net_amount": net_amount})

    @staticmethod
    def clear_calculation(employee_key: str) -> None:
        """Apaga a resposta deste funcionário. Sem ela, o MockServer devolve 404."""
        response = MockServerUtils.send(
            "/mockserver/clear", calculation_matcher(employee_key), params={"type": "EXPECTATIONS"}
        )
        assert response.status_code == 200, response.text

    @staticmethod
    def calculation_requests(employee_key: str) -> list:
        """As chamadas que a API fez para calcular este funcionário, na ordem."""
        response = MockServerUtils.send(
            "/mockserver/retrieve",
            calculation_matcher(employee_key),
            params={"type": "REQUESTS", "format": "JSON"},
        )
        assert response.status_code == 200, response.text

        return response.json()
