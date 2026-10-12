from concurrent.futures import ThreadPoolExecutor

from tests.utils import DbUtils, ObjectGenerator, RequestGenerator


NOT_FOUND_KEY = "00000000-0000-0000-0000-000000000000"


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


def transfers_received(account_key: str) -> list:
    status, response = RequestGenerator.GET_account_statement(account_key, {"limit": 100})
    assert status == 200

    transfers = []
    for entry in response["data"]:
        if entry["entry_type"] == "credit" and entry["transfer_key"] is not None:
            status, transfer = RequestGenerator.GET_transfer(entry["transfer_key"])
            assert status == 200
            transfers.append(transfer)
    return transfers


class TestPayrollPay:

    def test_pay_moves_money_to_settlement(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000], fee_amount=150)
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]

        status, response = RequestGenerator.PUT_payroll_pay(payroll_key)
        assert status == 202
        assert response == {"payroll_key": payroll_key, "status": "processing"}

        payroll = get_payroll(payroll_key)
        assert payroll["status"] == "processing"
        assert payroll["settlement_balance_amount"] == 780300
        assert payroll["paid_at"] is None
        assert [event["status"] for event in payroll["status_events"]] == ["pending", "processing"]

        assert balance(scenario["company_account_key"]) == 0
        assert balance(payroll["settlement_account_key"]) == 780300

    def test_pay_does_not_touch_employees_nor_bank(self):
        bank = DbUtils.bank_account_key()
        bank_before = balance(bank)
        scenario = ObjectGenerator.create_payroll_scenario()

        payroll = ObjectGenerator.create_processing_payroll(scenario)

        for employee in scenario["employees"]:
            assert balance(employee["account_key"]) == 0
            assert item_of(payroll, employee["employee_key"])["status"] == "pending"
        assert balance(bank) == bank_before

    def test_settlement_transfer_has_no_fee(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        payroll = ObjectGenerator.create_processing_payroll(scenario)

        transfers = transfers_received(payroll["settlement_account_key"])
        assert len(transfers) == 1
        assert transfers[0]["source_account_key"] == scenario["company_account_key"]
        assert transfers[0]["destination_account_key"] == payroll["settlement_account_key"]
        assert transfers[0]["amount"] == 780300
        assert transfers[0]["fee_amount"] == 0

    def test_refuses_insufficient_balance(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000], company_balance=780299)
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]

        status, response = RequestGenerator.PUT_payroll_pay(payroll_key)
        assert status == 422
        assert response["code"] == "QIT001028"

        payroll = get_payroll(payroll_key)
        assert payroll["status"] == "pending"
        assert payroll["settlement_account_key"] is None
        assert balance(scenario["company_account_key"]) == 780299

    def test_pays_after_balance_is_completed(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000], company_balance=780299)
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]

        status, _response = RequestGenerator.PUT_payroll_pay(payroll_key)
        assert status == 422

        ObjectGenerator.credit_account(scenario["company_account_key"], 1)
        ObjectGenerator.pay_payroll(payroll_key)

        assert balance(scenario["company_account_key"]) == 0

    def test_refuses_blocked_company_account(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]
        ObjectGenerator.update_account_status(scenario["company_account_key"], "blocked")

        status, response = RequestGenerator.PUT_payroll_pay(payroll_key)
        assert status == 422
        assert response["code"] == "QIT001024"

        assert get_payroll(payroll_key)["status"] == "pending"
        assert balance(scenario["company_account_key"]) == 780300

    def test_refuses_paying_twice(self):
        scenario = ObjectGenerator.create_payroll_scenario(company_balance=2000000)
        payroll = ObjectGenerator.create_processing_payroll(scenario)

        status, response = RequestGenerator.PUT_payroll_pay(payroll["payroll_key"])
        assert status == 422
        assert response["code"] == "QIT001036"

        assert balance(scenario["company_account_key"]) == 2000000 - 780300

    def test_refuses_paying_paid_payroll(self):
        scenario = ObjectGenerator.create_payroll_scenario(company_balance=2000000)
        payroll = ObjectGenerator.create_processing_payroll(scenario)
        ObjectGenerator.process_payroll(payroll["payroll_key"])

        status, response = RequestGenerator.PUT_payroll_pay(payroll["payroll_key"])
        assert status == 422
        assert response["code"] == "QIT001036"

    def test_refuses_paying_canceled_payroll(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]
        ObjectGenerator.cancel_payroll(payroll_key)

        status, response = RequestGenerator.PUT_payroll_pay(payroll_key)
        assert status == 422
        assert response["code"] == "QIT001036"

        assert balance(scenario["company_account_key"]) == 780300

    def test_concurrent_pay_debits_once(self):
        scenario = ObjectGenerator.create_payroll_scenario(company_balance=780300 * 5)
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda _: RequestGenerator.PUT_payroll_pay(payroll_key), range(5)))

        statuses = sorted(status for status, _response in results)
        assert statuses == [202, 422, 422, 422, 422]
        for status, response in results:
            if status == 422:
                assert response["code"] == "QIT001036"

        assert balance(scenario["company_account_key"]) == 780300 * 4
        assert get_payroll(payroll_key)["settlement_balance_amount"] == 780300

    def test_not_found(self):
        status, response = RequestGenerator.PUT_payroll_pay(NOT_FOUND_KEY)
        assert status == 404
        assert response["code"] == "QIT001030"


class TestPayrollProcess:
    def test_pays_every_employee(self):
        bank = DbUtils.bank_account_key()
        bank_before = balance(bank)
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000], fee_amount=150)
        payroll = ObjectGenerator.create_processing_payroll(scenario)

        status, response = RequestGenerator.POST_test_payroll_process(payroll["payroll_key"])
        assert status == 200
        assert response == {
            "payroll_key": payroll["payroll_key"],
            "status": "paid",
            "paid_items_count": 2,
            "failed_items_count": 0,
        }

        first, second = scenario["employees"]
        assert balance(first["account_key"]) == 400000
        assert balance(second["account_key"]) == 380000
        assert balance(bank) == bank_before + 300
        assert balance(scenario["company_account_key"]) == 0

    def test_finishes_payroll(self):
        payroll = ObjectGenerator.create_processing_payroll()
        ObjectGenerator.process_payroll(payroll["payroll_key"])

        payroll = get_payroll(payroll["payroll_key"])
        assert payroll["status"] == "paid"
        assert payroll["paid_at"] is not None
        assert payroll["settlement_balance_amount"] == 0
        assert [event["status"] for event in payroll["status_events"]] == ["pending", "processing", "paid"]
        for item in payroll["items"]:
            assert item["status"] == "paid"
            assert item["failure_reason"] is None

        status, settlement = RequestGenerator.GET_account(payroll["settlement_account_key"])
        assert status == 200
        assert settlement["balance_amount"] == 0
        assert settlement["status"] == "closed"

    def test_one_transfer_per_item(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000], fee_amount=150)
        payroll = ObjectGenerator.create_processing_payroll(scenario)
        ObjectGenerator.process_payroll(payroll["payroll_key"])

        for employee in scenario["employees"]:
            transfers = transfers_received(employee["account_key"])
            assert len(transfers) == 1
            assert transfers[0]["source_account_key"] == payroll["settlement_account_key"]
            assert transfers[0]["destination_account_key"] == employee["account_key"]
            assert transfers[0]["amount"] == employee["net_amount"]
            assert transfers[0]["fee_amount"] == 150

    def test_uses_fee_frozen_on_creation(self):
        bank = DbUtils.bank_account_key()
        bank_before = balance(bank)
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000], fee_amount=150)
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]

        status, _response = RequestGenerator.PUT_company(scenario["company_key"], {"fee_amount": 900})
        assert status == 202

        ObjectGenerator.pay_payroll(payroll_key)
        ObjectGenerator.process_payroll(payroll_key)

        assert balance(bank) == bank_before + 150
        assert balance(scenario["employees"][0]["account_key"]) == 400000

    def test_processing_twice_pays_once(self):
        bank = DbUtils.bank_account_key()
        scenario = ObjectGenerator.create_payroll_scenario()
        payroll = ObjectGenerator.create_processing_payroll(scenario)
        ObjectGenerator.process_payroll(payroll["payroll_key"])
        bank_after_first = balance(bank)

        response = ObjectGenerator.process_payroll(payroll["payroll_key"])
        assert response["status"] == "paid"
        assert response["paid_items_count"] == 2

        for employee in scenario["employees"]:
            assert balance(employee["account_key"]) == employee["net_amount"]
        assert balance(bank) == bank_after_first

    def test_concurrent_processing_pays_once(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000, 360000, 340000])
        payroll = ObjectGenerator.create_processing_payroll(scenario)

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(
                executor.map(lambda _: RequestGenerator.POST_test_payroll_process(payroll["payroll_key"]), range(4))
            )

        assert [status for status, _response in results] == [200, 200, 200, 200]

        for employee in scenario["employees"]:
            assert balance(employee["account_key"]) == employee["net_amount"]
        assert get_payroll(payroll["payroll_key"])["status"] == "paid"
        assert balance(payroll["settlement_account_key"]) == 0

    def test_pending_payroll_is_not_processed(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]

        response = ObjectGenerator.process_payroll(payroll_key)
        assert response["status"] == "pending"
        assert response["paid_items_count"] == 0

        for employee in scenario["employees"]:
            assert balance(employee["account_key"]) == 0
        assert balance(scenario["company_account_key"]) == 780300

    def test_canceled_payroll_is_not_processed(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]
        ObjectGenerator.cancel_payroll(payroll_key)

        response = ObjectGenerator.process_payroll(payroll_key)
        assert response["status"] == "canceled"
        assert response["paid_items_count"] == 0

        for employee in scenario["employees"]:
            assert balance(employee["account_key"]) == 0

    def test_blocked_employee_account_fails_only_its_item(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000], fee_amount=150)
        paid, failed = scenario["employees"]
        payroll = ObjectGenerator.create_processing_payroll(scenario)
        ObjectGenerator.update_account_status(failed["account_key"], "blocked")

        response = ObjectGenerator.process_payroll(payroll["payroll_key"])
        assert response["status"] == "processing"
        assert response["paid_items_count"] == 1
        assert response["failed_items_count"] == 1

        payroll = get_payroll(payroll["payroll_key"])
        assert payroll["status"] == "processing"
        assert payroll["paid_at"] is None
        assert payroll["settlement_balance_amount"] == 380150
        assert item_of(payroll, paid["employee_key"])["status"] == "paid"

        failed_item = item_of(payroll, failed["employee_key"])
        assert failed_item["status"] == "failed"
        assert failed_item["failure_reason"]

        assert balance(paid["account_key"]) == 400000
        assert balance(failed["account_key"]) == 0

    def test_money_is_conserved(self):
        bank = DbUtils.bank_account_key()
        bank_before = balance(bank)
        scenario = ObjectGenerator.create_payroll_scenario(
            net_amounts=[400000, 380000, 123457], fee_amount=275, company_balance=2000000
        )
        payroll = ObjectGenerator.create_processing_payroll(scenario)
        ObjectGenerator.process_payroll(payroll["payroll_key"])

        employees_total = sum(balance(employee["account_key"]) for employee in scenario["employees"])
        company_debit = 2000000 - balance(scenario["company_account_key"])
        bank_credit = balance(bank) - bank_before

        assert employees_total == 903457
        assert bank_credit == 825
        assert company_debit == employees_total + bank_credit
        assert balance(payroll["settlement_account_key"]) == 0

    def test_not_found(self):
        status, response = RequestGenerator.POST_test_payroll_process(NOT_FOUND_KEY)
        assert status == 404
        assert response["code"] == "QIT001030"
