from tests.utils import ObjectGenerator, RequestGenerator


NOT_FOUND_KEY = "00000000-0000-0000-0000-000000000000"
PAYROLL_FIELDS = {
    "payroll_key",
    "company_key",
    "reference_month",
    "status",
    "total_amount",
    "total_fee_amount",
    "settlement_account_key",
    "settlement_balance_amount",
    "paid_at",
    "status_events",
    "items",
    "created_at",
}
ITEM_FIELDS = {"employee_key", "gross_amount", "net_amount", "fee_amount", "status", "failure_reason"}


class TestPayrollGet:
    def test_gets_new_payroll(self):
        """O rascunho ainda nao tem conta de liquidacao nem data de pagamento."""
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000])
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"], "2026-09")["payroll_key"]

        status, response = RequestGenerator.GET_payroll(payroll_key)
        assert status == 200
        assert response["payroll_key"] == payroll_key
        assert response["company_key"] == scenario["company_key"]
        assert response["reference_month"] == "2026-09"
        assert response["status"] == "pending"
        assert response["total_amount"] == 780000
        assert response["total_fee_amount"] == 300
        assert response["settlement_account_key"] is None
        assert response["settlement_balance_amount"] is None
        assert response["paid_at"] is None
        assert [event["status"] for event in response["status_events"]] == ["pending"]

        assert len(response["items"]) == 2
        for item in response["items"]:
            assert item["status"] == "pending"
            assert item["failure_reason"] is None

    def test_does_not_expose_internal_fields(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]

        status, response = RequestGenerator.GET_payroll(payroll_key)
        assert status == 200
        assert set(response.keys()) == PAYROLL_FIELDS
        for item in response["items"]:
            assert set(item.keys()) == ITEM_FIELDS

    def test_shows_settlement_while_processing(self):
        payroll = ObjectGenerator.create_processing_payroll()

        status, response = RequestGenerator.GET_payroll(payroll["payroll_key"])
        assert status == 200
        assert response["status"] == "processing"
        assert response["settlement_account_key"] is not None
        assert response["settlement_balance_amount"] == 780300

        status, account = RequestGenerator.GET_account(response["settlement_account_key"])
        assert status == 200
        assert account["account_type"] == "settlement"
        assert account["balance_amount"] == 780300

    def test_not_found(self):
        status, response = RequestGenerator.GET_payroll(NOT_FOUND_KEY)
        assert status == 404
        assert response["code"] == "QIT001030"

    def test_company_key_is_not_found(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        ObjectGenerator.create_payroll(scenario["company_key"])

        status, response = RequestGenerator.GET_payroll(scenario["company_key"])
        assert status == 404
        assert response["code"] == "QIT001030"
