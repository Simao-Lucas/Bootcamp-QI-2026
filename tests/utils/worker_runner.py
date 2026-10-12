import subprocess
import sys
from os import environ
from pathlib import Path

from tests.utils.db_utils import DbUtils


SRC_DIR = Path(__file__).resolve().parents[2] / "src"


class WorkerRunner:
    """Roda o worker da folha de verdade, como processo, na sua máquina.

    É o `src/worker.py --once`: paga tudo o que houver e sai. Ele fala
    direto com o mesmo banco da API, pela DATABASE_URL dos testes, sem
    passar pela API. "Tudo o que houver" inclui folhas que outros testes
    deixaram em processing, porque o banco é compartilhado: quem testa o
    worker olha só a própria folha.
    """

    @staticmethod
    def start(batch_size: int = None) -> subprocess.Popen:
        env = dict(environ)
        env["DATABASE_URL"] = DbUtils.database_url()
        env["PYTHONIOENCODING"] = "utf-8"
        if batch_size is not None:
            env["PAYROLL_BATCH_SIZE"] = str(batch_size)

        return subprocess.Popen(
            [sys.executable, "worker.py", "--once"],
            cwd=SRC_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
        )

    @staticmethod
    def wait(process: subprocess.Popen) -> str:
        """Espera o worker sair e devolve o log dele. Saída com erro falha o teste."""
        output, _ = process.communicate(timeout=120)
        assert process.returncode == 0, output

        return output

    @staticmethod
    def run_until_idle(batch_size: int = None) -> str:
        return WorkerRunner.wait(WorkerRunner.start(batch_size))
