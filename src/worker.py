import argparse
import signal
import threading
from uuid import uuid4

from constants import WORKER_INTERVAL_SECONDS, WORKER_REQUIRED_VARIABLES, check_variables
from controllers import PayrollController
from database import clear_context, open_context
from utils.logger import get_logger, setup_logging
from utils.request_context import NO_REQUEST_ID, set_request_id

logger = get_logger(__name__)


class PayrollWorker:
    def __init__(self, interval_seconds: float) -> None:
        self.interval_seconds = interval_seconds
        self.stop_requested = threading.Event()

    def run_forever(self) -> None:
        logger.info(f"Worker da folha de pé, procurando lotes a cada {self.interval_seconds} s")

        while not self.stop_requested.is_set():
            if not self.run_cycle():
                self.stop_requested.wait(self.interval_seconds)

        logger.info("Worker da folha parado")

    def run_until_idle(self) -> int:
        batches_count = 0

        while self.run_cycle():
            batches_count = batches_count + 1

        return batches_count

    def run_cycle(self) -> bool:
        set_request_id(f"worker-{uuid4()}")
        context = open_context()

        try:
            controller = PayrollController()
            payroll_key = controller.pay_next_batch()
        except Exception:
            logger.exception("O lote falhou e foi desfeito")

            if context.db_session is not None:
                context.db_session.rollback()

            return False
        finally:
            if context.db_session is not None:
                context.db_session.close()

            clear_context()
            set_request_id(NO_REQUEST_ID)

        return payroll_key is not None

    def stop(self, signal_number, frame) -> None:
        logger.info("Parada pedida: o worker sai depois do lote em andamento")
        self.stop_requested.set()


def main() -> None:
    parser = argparse.ArgumentParser(description="Worker que paga as folhas em processing, em lotes.")
    parser.add_argument("--once", action="store_true", help="paga tudo o que houver e sai")
    args = parser.parse_args()

    check_variables(WORKER_REQUIRED_VARIABLES)
    setup_logging()

    worker = PayrollWorker(WORKER_INTERVAL_SECONDS)

    if args.once:
        batches_count = worker.run_until_idle()
        logger.info(f"Nada mais para pagar: {batches_count} lotes pagos")
        return

    signal.signal(signal.SIGTERM, worker.stop)
    signal.signal(signal.SIGINT, worker.stop)

    worker.run_forever()


if __name__ == "__main__":
    main()
