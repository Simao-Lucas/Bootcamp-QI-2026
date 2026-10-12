from tests.utils import ObjectGenerator, RequestGenerator


NOT_FOUND_KEY = "00000000-0000-0000-0000-000000000000"


class TestPayrollCancel:
    def test_cancels_pending_payroll(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]

        status, response = RequestGenerator.PUT_payroll_cancel(payroll_key)
        assert status == 202
        assert response == {"payroll_key": payroll_key}

        status, response = RequestGenerator.GET_payroll(payroll_key)
        assert response["status"] == "canceled"
        assert [event["status"] for event in response["status_events"]] == ["pending", "canceled"]

    def test_cancel_moves_no_money(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]

        ObjectGenerator.cancel_payroll(payroll_key)

        status, response = RequestGenerator.GET_account(scenario["company_account_key"])
        assert response["balance_amount"] == 780300

    def test_refuses_canceling_twice(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]
        ObjectGenerator.cancel_payroll(payroll_key)

        status, response = RequestGenerator.PUT_payroll_cancel(payroll_key)
        assert status == 422
        assert response["code"] == "QIT001036"

    def test_refuses_canceling_processing_payroll(self):
        payroll = ObjectGenerator.create_processing_payroll()

        status, response = RequestGenerator.PUT_payroll_cancel(payroll["payroll_key"])
        assert status == 422
        assert response["code"] == "QIT001036"

        status, response = RequestGenerator.GET_payroll(payroll["payroll_key"])
        assert response["status"] == "processing"
        assert response["settlement_balance_amount"] == 780300

    def test_refuses_canceling_paid_payroll(self):
        payroll = ObjectGenerator.create_processing_payroll()
        ObjectGenerator.process_payroll(payroll["payroll_key"])

        status, response = RequestGenerator.PUT_payroll_cancel(payroll["payroll_key"])
        assert status == 422
        assert response["code"] == "QIT001036"

    def test_not_found(self):
        status, response = RequestGenerator.PUT_payroll_cancel(NOT_FOUND_KEY)
        assert status == 404
        assert response["code"] == "QIT001030"
