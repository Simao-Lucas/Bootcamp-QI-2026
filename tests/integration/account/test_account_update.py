from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


def current_status(account_key: str) -> str:
    status, response = RequestGenerator.GET_account(account_key)
    assert status == 200
    return response["status"]


class TestAccountUpdate:
    def test_refuses_empty_body(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        status, response = RequestGenerator.PUT_account(account_key, {})
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_unknown_status(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        for status_torto in ["frozen", "ACTIVE", "", None]:
            payload = PayloadGenerator.create_account_status_payload(status_torto)

            status, response = RequestGenerator.PUT_account(account_key, payload)

            assert status == 400, f"aceitou o status {status_torto!r}"
            assert response["code"] == "QIT000001"

    def test_schema_refuses_unknown_field(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        status, response = RequestGenerator.PUT_account(
            account_key, {"status": "blocked", "balance_amount": 999999}
        )
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_blocks_account(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        status, response = RequestGenerator.PUT_account(
            account_key, PayloadGenerator.create_account_status_payload("blocked")
        )
        assert status == 202
        assert response["account_key"] == account_key

        assert current_status(account_key) == "blocked"

    def test_reactivates_blocked_account(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.update_account_status(account_key, "blocked")

        status, _response = RequestGenerator.PUT_account(
            account_key, PayloadGenerator.create_account_status_payload("active")
        )
        assert status == 202

        assert current_status(account_key) == "active"

    def test_closes_account_without_balance(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        status, _response = RequestGenerator.PUT_account(
            account_key, PayloadGenerator.create_account_status_payload("closed")
        )
        assert status == 202

        assert current_status(account_key) == "closed"

    def test_closes_blocked_account(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.update_account_status(account_key, "blocked")

        status, _response = RequestGenerator.PUT_account(
            account_key, PayloadGenerator.create_account_status_payload("closed")
        )
        assert status == 202

        assert current_status(account_key) == "closed"

    def test_refuses_closing_account_with_balance(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.credit_account(account_key, 1)

        status, response = RequestGenerator.PUT_account(
            account_key, PayloadGenerator.create_account_status_payload("closed")
        )
        assert status == 422
        assert response["code"] == "QIT001023"

        assert current_status(account_key) == "active"

    def test_closed_account_cannot_change(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.update_account_status(account_key, "closed")

        for new_status in ["active", "blocked", "closed"]:
            status, response = RequestGenerator.PUT_account(
                account_key, PayloadGenerator.create_account_status_payload(new_status)
            )

            assert status == 422, f"mudou uma conta encerrada para '{new_status}'"
            assert response["code"] == "QIT001022"

        assert current_status(account_key) == "closed"

    def test_status_events_keep_the_trail_in_order(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        ObjectGenerator.update_account_status(account_key, "blocked")
        ObjectGenerator.update_account_status(account_key, "active")
        ObjectGenerator.update_account_status(account_key, "closed")

        status, _response = RequestGenerator.PUT_account(
            account_key, PayloadGenerator.create_account_status_payload("active")
        )
        assert status == 422

        status, response = RequestGenerator.GET_account(account_key)
        assert status == 200

        statuses = [event["status"] for event in response["status_events"]]
        assert statuses == ["active", "blocked", "active", "closed"]

    def test_not_found(self):
        status, response = RequestGenerator.PUT_account(
            "00000000-0000-0000-0000-000000000000",
            PayloadGenerator.create_account_status_payload("blocked"),
        )
        assert status == 404
        assert response["code"] == "QIT001021"
