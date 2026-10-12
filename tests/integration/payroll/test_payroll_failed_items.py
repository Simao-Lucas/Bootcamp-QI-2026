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


def create_payroll_with_failed_item(account_status: str = "blocked") -> dict:
    scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000], fee_amount=150)
    payroll = ObjectGenerator.create_processing_payroll(scenario)
    ObjectGenerator.update_account_status(scenario["employees"][1]["account_key"], account_status)

    response = ObjectGenerator.process_payroll(payroll["payroll_key"])
    assert response["failed_items_count"] == 1

    return {
        "scenario": scenario,
        "payroll_key": payroll["payroll_key"],
        "settlement_account_key": payroll["settlement_account_key"],
        "paid": scenario["employees"][0],
        "failed": scenario["employees"][1],
    }


class TestPayrollRetry:
    def test_retry_after_reactivation_pays_the_item(self):
        case = create_payroll_with_failed_item()
        ObjectGenerator.update_account_status(case["failed"]["account_key"], "active")

        status, response = RequestGenerator.PUT_payroll_retry(case["payroll_key"])
        assert status == 202
        assert response == {"payroll_key": case["payroll_key"], "retried_items_count": 1}

        payroll = get_payroll(case["payroll_key"])
        assert payroll["status"] == "processing"
        assert item_of(payroll, case["failed"]["employee_key"])["status"] == "pending"

        response = ObjectGenerator.process_payroll(case["payroll_key"])
        assert response["status"] == "paid"
        assert response["paid_items_count"] == 2
        assert response["failed_items_count"] == 0

        assert balance(case["failed"]["account_key"]) == 380000
        assert balance(case["paid"]["account_key"]) == 400000
        assert balance(case["settlement_account_key"]) == 0

    def test_retry_clears_failure_reason(self):
        case = create_payroll_with_failed_item()
        ObjectGenerator.update_account_status(case["failed"]["account_key"], "active")

        status, _response = RequestGenerator.PUT_payroll_retry(case["payroll_key"])
        assert status == 202
        ObjectGenerator.process_payroll(case["payroll_key"])

        item = item_of(get_payroll(case["payroll_key"]), case["failed"]["employee_key"])
        assert item["status"] == "paid"
        assert item["failure_reason"] is None

    def test_retry_does_not_move_money(self):
        case = create_payroll_with_failed_item()

        status, _response = RequestGenerator.PUT_payroll_retry(case["payroll_key"])
        assert status == 202

        assert balance(case["settlement_account_key"]) == 380150
        assert balance(case["failed"]["account_key"]) == 0

    def test_retry_without_fixing_the_account_fails_again(self):
        case = create_payroll_with_failed_item()

        status, _response = RequestGenerator.PUT_payroll_retry(case["payroll_key"])
        assert status == 202

        response = ObjectGenerator.process_payroll(case["payroll_key"])
        assert response["status"] == "processing"
        assert response["failed_items_count"] == 1

        assert balance(case["settlement_account_key"]) == 380150
        assert balance(case["paid"]["account_key"]) == 400000

    def test_refuses_payroll_without_failed_items(self):
        payroll = ObjectGenerator.create_processing_payroll()

        status, response = RequestGenerator.PUT_payroll_retry(payroll["payroll_key"])
        assert status == 422
        assert response["code"] == "QIT001038"

    def test_refuses_payroll_that_is_not_processing(self):
        scenario = ObjectGenerator.create_payroll_scenario(company_balance=2000000)
        pending_key = ObjectGenerator.create_payroll(scenario["company_key"], "2026-08")["payroll_key"]
        canceled_key = ObjectGenerator.create_payroll(scenario["company_key"], "2026-09")["payroll_key"]
        ObjectGenerator.cancel_payroll(canceled_key)
        paid_key = ObjectGenerator.create_payroll(scenario["company_key"], "2026-10")["payroll_key"]
        ObjectGenerator.pay_payroll(paid_key)
        ObjectGenerator.process_payroll(paid_key)

        for payroll_key in [pending_key, canceled_key, paid_key]:
            status, response = RequestGenerator.PUT_payroll_retry(payroll_key)

            assert status == 422
            assert response["code"] == "QIT001037"

    def test_not_found(self):
        status, response = RequestGenerator.PUT_payroll_retry(NOT_FOUND_KEY)
        assert status == 404
        assert response["code"] == "QIT001030"


class TestPayrollRefund:

    def test_refund_returns_money_to_company(self):
        case = create_payroll_with_failed_item("closed")
        company_account_key = case["scenario"]["company_account_key"]

        status, response = RequestGenerator.PUT_payroll_refund(case["payroll_key"])
        assert status == 202
        assert response == {"payroll_key": case["payroll_key"], "refunded_amount": 380150}

        assert balance(company_account_key) == 380150
        assert balance(case["settlement_account_key"]) == 0
        assert balance(case["failed"]["account_key"]) == 0

    def test_refund_finishes_payroll(self):
        case = create_payroll_with_failed_item("closed")

        status, _response = RequestGenerator.PUT_payroll_refund(case["payroll_key"])
        assert status == 202

        payroll = get_payroll(case["payroll_key"])
        assert payroll["status"] == "paid"
        assert payroll["paid_at"] is not None
        assert payroll["settlement_balance_amount"] == 0
        assert [event["status"] for event in payroll["status_events"]] == ["pending", "processing", "paid"]
        assert item_of(payroll, case["paid"]["employee_key"])["status"] == "paid"
        assert item_of(payroll, case["failed"]["employee_key"])["status"] == "refunded"

        status, settlement = RequestGenerator.GET_account(case["settlement_account_key"])
        assert settlement["status"] == "closed"

    def test_refund_transfer_has_no_fee(self):
        bank = DbUtils.bank_account_key()
        case = create_payroll_with_failed_item("closed")
        company_account_key = case["scenario"]["company_account_key"]
        bank_before = balance(bank)

        status, _response = RequestGenerator.PUT_payroll_refund(case["payroll_key"])
        assert status == 202

        status, statement = RequestGenerator.GET_account_statement(company_account_key)
        assert status == 200
        refund_entry = statement["data"][0]
        assert refund_entry["entry_type"] == "credit"
        assert refund_entry["amount"] == 380150

        status, transfer = RequestGenerator.GET_transfer(refund_entry["transfer_key"])
        assert status == 200
        assert transfer["source_account_key"] == case["settlement_account_key"]
        assert transfer["destination_account_key"] == company_account_key
        assert transfer["fee_amount"] == 0

        assert balance(bank) == bank_before

    def test_money_is_conserved(self):
        bank = DbUtils.bank_account_key()
        bank_before = balance(bank)
        case = create_payroll_with_failed_item("closed")

        status, _response = RequestGenerator.PUT_payroll_refund(case["payroll_key"])
        assert status == 202

        company_debit = 780300 - balance(case["scenario"]["company_account_key"])
        assert company_debit == 400150
        assert balance(case["paid"]["account_key"]) + (balance(bank) - bank_before) == company_debit

    def test_refuses_blocked_company_account(self):
        case = create_payroll_with_failed_item("closed")
        ObjectGenerator.update_account_status(case["scenario"]["company_account_key"], "blocked")

        status, response = RequestGenerator.PUT_payroll_refund(case["payroll_key"])
        assert status == 422
        assert response["code"] == "QIT001024"

        payroll = get_payroll(case["payroll_key"])
        assert payroll["status"] == "processing"
        assert item_of(payroll, case["failed"]["employee_key"])["status"] == "failed"
        assert balance(case["settlement_account_key"]) == 380150

    def test_refuses_payroll_without_failed_items(self):
        payroll = ObjectGenerator.create_processing_payroll()

        status, response = RequestGenerator.PUT_payroll_refund(payroll["payroll_key"])
        assert status == 422
        assert response["code"] == "QIT001038"

        assert balance(payroll["settlement_account_key"]) == 780300

    def test_refuses_refunding_twice(self):
        case = create_payroll_with_failed_item("closed")

        status, _response = RequestGenerator.PUT_payroll_refund(case["payroll_key"])
        assert status == 202

        status, response = RequestGenerator.PUT_payroll_refund(case["payroll_key"])
        assert status == 422
        assert response["code"] == "QIT001037"

        assert balance(case["scenario"]["company_account_key"]) == 380150

    def test_refuses_payroll_that_is_not_processing(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]

        status, response = RequestGenerator.PUT_payroll_refund(payroll_key)
        assert status == 422
        assert response["code"] == "QIT001037"

    def test_not_found(self):
        status, response = RequestGenerator.PUT_payroll_refund(NOT_FOUND_KEY)
        assert status == 404
        assert response["code"] == "QIT001030"
