from pathlib import Path
from os import path, environ

import pytest

root = Path(__file__).resolve().parents[1]

if not environ.get("APP_ENV") or environ.get("APP_ENV") == "local":
    from dotenv import load_dotenv

    load_dotenv(path.join(str(root), ".env"))

    if environ.get("SERVER_LOCALHOST") is None:
        environ["SERVER_LOCALHOST"] = "0.0.0.0"


@pytest.fixture(scope="session", autouse=True)
def reset_mock_server():
    # Importado aqui, e não no topo, porque o mock_server lê a MOCKSERVER_URL
    # na importação, e ela só existe depois do load_dotenv acima.
    from tests.utils import MockServerUtils

    MockServerUtils.reset()
