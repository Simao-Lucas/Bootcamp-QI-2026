from tests.utils import DbUtils, ObjectGenerator, RequestGenerator, WorkerRunner


def balance(account_key: str) -> int:
    status, response = RequestGenerator.GET_account(account_key)
    assert status == 200
    return response["balance_amount"]


def item_of(payroll: dict, employee_key: str) -> dict:
    for item in payroll["items"]:
        if item["employee_key"] == employee_key:
            return item
    raise AssertionError(f"o funcionario {employee_key} nao esta na folha")


def get_payroll(payroll_key: str) -> dict:
    status, response = RequestGenerator.GET_payroll(payroll_key)
    assert status == 200
    return response


def drained_bank_balance(bank: str) -> int:
    WorkerRunner.run_until_idle()
    return balance(bank)


def batches_of(worker_log: str, payroll_key: str) -> int:
    return worker_log.count(f"Lote da folha {payroll_key}")


class TestPayrollWorker:
    def test_pays_processing_payroll(self):
        bank = DbUtils.bank_account_key()
        bank_before = drained_bank_balance(bank)
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000], fee_amount=150)
        payroll = ObjectGenerator.create_processing_payroll(scenario)

        WorkerRunner.run_until_idle()

        payroll = get_payroll(payroll["payroll_key"])
        assert payroll["status"] == "paid"
        assert payroll["paid_at"] is not None
        assert payroll["settlement_balance_amount"] == 0

        for employee in scenario["employees"]:
            assert balance(employee["account_key"]) == employee["net_amount"]
        assert balance(bank) == bank_before + 300

        status, settlement = RequestGenerator.GET_account(payroll["settlement_account_key"])
        assert settlement["status"] == "closed"

    def test_does_not_pay_pending_payroll(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]

        worker_log = WorkerRunner.run_until_idle()

        assert get_payroll(payroll_key)["status"] == "pending"
        assert batches_of(worker_log, payroll_key) == 0
        for employee in scenario["employees"]:
            assert balance(employee["account_key"]) == 0

    def test_pays_in_batches(self):
        scenario = ObjectGenerator.create_payroll_scenario(
            net_amounts=[400000, 380000, 360000, 340000, 320000]
        )
        payroll = ObjectGenerator.create_processing_payroll(scenario)

        worker_log = WorkerRunner.run_until_idle(batch_size=2)

        assert batches_of(worker_log, payroll["payroll_key"]) == 3
        assert get_payroll(payroll["payroll_key"])["status"] == "paid"
        for employee in scenario["employees"]:
            assert balance(employee["account_key"]) == employee["net_amount"]

    def test_failed_item_does_not_stop_the_worker(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000], fee_amount=150)
        paid, failed = scenario["employees"]
        payroll = ObjectGenerator.create_processing_payroll(scenario)
        ObjectGenerator.update_account_status(failed["account_key"], "blocked")

        WorkerRunner.run_until_idle()

        payroll = get_payroll(payroll["payroll_key"])
        assert payroll["status"] == "processing"
        assert payroll["settlement_balance_amount"] == 380150
        assert item_of(payroll, paid["employee_key"])["status"] == "paid"

        failed_item = item_of(payroll, failed["employee_key"])
        assert failed_item["status"] == "failed"
        assert failed_item["failure_reason"]

        assert balance(paid["account_key"]) == 400000
        assert balance(failed["account_key"]) == 0

    def test_pays_retried_items(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000])
        failed = scenario["employees"][1]
        payroll = ObjectGenerator.create_processing_payroll(scenario)
        ObjectGenerator.update_account_status(failed["account_key"], "blocked")
        WorkerRunner.run_until_idle()

        ObjectGenerator.update_account_status(failed["account_key"], "active")
        status, _response = RequestGenerator.PUT_payroll_retry(payroll["payroll_key"])
        assert status == 202

        WorkerRunner.run_until_idle()

        assert get_payroll(payroll["payroll_key"])["status"] == "paid"
        assert balance(failed["account_key"]) == 380000

    def test_two_workers_pay_each_item_once(self):
        bank = DbUtils.bank_account_key()
        bank_before = drained_bank_balance(bank)
        scenario = ObjectGenerator.create_payroll_scenario(
            net_amounts=[400000, 380000, 360000, 340000], fee_amount=150
        )
        payroll = ObjectGenerator.create_processing_payroll(scenario)

        first = WorkerRunner.start(batch_size=1)
        second = WorkerRunner.start(batch_size=1)
        first_log = WorkerRunner.wait(first)
        second_log = WorkerRunner.wait(second)

        payroll_key = payroll["payroll_key"]
        assert batches_of(first_log, payroll_key) + batches_of(second_log, payroll_key) == 4

        assert get_payroll(payroll_key)["status"] == "paid"
        for employee in scenario["employees"]:
            assert balance(employee["account_key"]) == employee["net_amount"]
        assert balance(bank) == bank_before + 600
