from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


class TestAccountCredit:
    def test_refuses_empty_body(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        status, response = RequestGenerator.POST_test_credit(account_key, {})
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_unknown_field(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        payload = PayloadGenerator.create_credit_payload()
        payload["fee_amount"] = 0

        status, response = RequestGenerator.POST_test_credit(account_key, payload)
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_malformed_amount(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        for amount in ["100000", 1000.5, None, 0, -100]:
            payload = PayloadGenerator.create_credit_payload()
            payload["amount"] = amount

            status, response = RequestGenerator.POST_test_credit(account_key, payload)

            assert status == 400, f"aceitou o valor {amount!r}"
            assert response["code"] == "QIT000001"

    def test_credits_account(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        status, response = RequestGenerator.POST_test_credit(
            account_key, PayloadGenerator.create_credit_payload(100000)
        )
        assert status == 201
        assert response["balance_amount"] == 100000

        status, response = RequestGenerator.GET_account(account_key)
        assert response["balance_amount"] == 100000

    def test_credits_accumulate(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        ObjectGenerator.credit_account(account_key, 100000)

        status, response = RequestGenerator.POST_test_credit(
            account_key, PayloadGenerator.create_credit_payload(1)
        )
        assert status == 201
        assert response["balance_amount"] == 100001

    def test_accepts_minimum_amount(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        status, response = RequestGenerator.POST_test_credit(
            account_key, PayloadGenerator.create_credit_payload(1)
        )
        assert status == 201
        assert response["balance_amount"] == 1

    def test_credits_employee_account(self):
        account_key = ObjectGenerator.create_employee_account()["account_key"]

        status, response = RequestGenerator.POST_test_credit(
            account_key, PayloadGenerator.create_credit_payload(50000)
        )
        assert status == 201
        assert response["balance_amount"] == 50000

    def test_credits_only_the_requested_account(self):
        primeira = ObjectGenerator.create_company_account()["account_key"]
        segunda = ObjectGenerator.create_company_account()["account_key"]

        ObjectGenerator.credit_account(primeira, 100000)

        status, response = RequestGenerator.GET_account(segunda)
        assert response["balance_amount"] == 0

    def test_not_found(self):
        status, response = RequestGenerator.POST_test_credit(
            "00000000-0000-0000-0000-000000000000", PayloadGenerator.create_credit_payload()
        )
        assert status == 404
        assert response["code"] == "QIT001021"

    def test_refuses_blocked_account(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.update_account_status(account_key, "blocked")

        status, response = RequestGenerator.POST_test_credit(
            account_key, PayloadGenerator.create_credit_payload()
        )
        assert status == 422
        assert response["code"] == "QIT001024"

        status, response = RequestGenerator.GET_account(account_key)
        assert response["balance_amount"] == 0

    def test_refuses_closed_account(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.update_account_status(account_key, "closed")

        status, response = RequestGenerator.POST_test_credit(
            account_key, PayloadGenerator.create_credit_payload()
        )
        assert status == 422
        assert response["code"] == "QIT001024"

    def test_reactivated_account_receives_again(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.update_account_status(account_key, "blocked")
        ObjectGenerator.update_account_status(account_key, "active")

        status, response = RequestGenerator.POST_test_credit(
            account_key, PayloadGenerator.create_credit_payload(700)
        )
        assert status == 201
        assert response["balance_amount"] == 700
