from tests.utils import ObjectGenerator, RequestGenerator


ACCOUNT_FIELDS = {
    "account_key",
    "account_type",
    "company_key",
    "employee_key",
    "balance_amount",
    "status",
    "status_events",
}


class TestAccountGet:
    def test_gets_new_account(self):
        company_key = ObjectGenerator.create_company()["company_key"]
        account_key = ObjectGenerator.create_company_account(company_key)["account_key"]

        status, response = RequestGenerator.GET_account(account_key)
        assert status == 200
        assert response["account_key"] == account_key
        assert response["account_type"] == "company"
        assert response["company_key"] == company_key
        assert response["employee_key"] is None
        assert response["balance_amount"] == 0
        assert response["status"] == "active"
        assert len(response["status_events"]) == 1
        assert response["status_events"][0]["status"] == "active"
        assert "event_datetime" in response["status_events"][0]

    def test_does_not_expose_internal_fields(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        status, response = RequestGenerator.GET_account(account_key)
        assert status == 200
        assert set(response.keys()) == ACCOUNT_FIELDS

    def test_shows_current_balance(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        ObjectGenerator.credit_account(account_key, 100000)
        ObjectGenerator.credit_account(account_key, 2550)

        status, response = RequestGenerator.GET_account(account_key)
        assert status == 200
        assert response["balance_amount"] == 102550

    def test_not_found(self):
        status, response = RequestGenerator.GET_account("00000000-0000-0000-0000-000000000000")
        assert status == 404
        assert response["code"] == "QIT001021"

    def test_key_of_the_owner_is_not_found(self):
        company_key = ObjectGenerator.create_company()["company_key"]
        ObjectGenerator.create_company_account(company_key)

        status, response = RequestGenerator.GET_account(company_key)
        assert status == 404
        assert response["code"] == "QIT001021"
