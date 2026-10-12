from datetime import date, timedelta

from tests.utils import ObjectGenerator, RequestGenerator


NOT_FOUND_KEY = "00000000-0000-0000-0000-000000000000"
ENTRY_FIELDS = {"origin", "entry_type", "amount", "balance_after", "transfer_key", "created_at"}


def days_from_today(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def extract_amounts(response: dict) -> list:
    amounts = []
    for entry in response["data"]:
        amounts.append(entry["amount"])
    return amounts


class TestAccountStatement:
    def test_empty_statement(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        status, response = RequestGenerator.GET_account_statement(account_key)
        assert status == 200
        assert response["data"] == []
        assert response["is_last_page"] is True

    def test_test_credit_entry(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.credit_account(account_key, 100000)

        status, response = RequestGenerator.GET_account_statement(account_key)
        assert status == 200
        assert len(response["data"]) == 1

        entry = response["data"][0]
        assert set(entry.keys()) == ENTRY_FIELDS
        assert entry["origin"] == "test_credit"
        assert entry["entry_type"] == "credit"
        assert entry["amount"] == 100000
        assert entry["balance_after"] == 100000
        assert entry["transfer_key"] is None

    def test_lists_newest_first_with_running_balance(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        ObjectGenerator.credit_account(account_key, 100)
        ObjectGenerator.credit_account(account_key, 250)
        ObjectGenerator.credit_account(account_key, 1000)

        status, response = RequestGenerator.GET_account_statement(account_key)
        assert status == 200
        assert extract_amounts(response) == [1000, 250, 100]

        balances = [entry["balance_after"] for entry in response["data"]]
        assert balances == [1350, 350, 100]

    def test_get_pages(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        for amount in [100, 200, 300]:
            ObjectGenerator.credit_account(account_key, amount)

        status, response = RequestGenerator.GET_account_statement(account_key, {"limit": 2})
        assert status == 200
        assert extract_amounts(response) == [300, 200]
        assert response["is_last_page"] is False

        status, response = RequestGenerator.GET_account_statement(account_key, {"limit": 2, "page": 1})
        assert status == 200
        assert extract_amounts(response) == [100]
        assert response["is_last_page"] is True

    def test_lists_only_entries_of_the_account(self):
        primeira = ObjectGenerator.create_company_account()["account_key"]
        segunda = ObjectGenerator.create_company_account()["account_key"]

        ObjectGenerator.credit_account(primeira, 100)
        ObjectGenerator.credit_account(segunda, 999)

        status, response = RequestGenerator.GET_account_statement(primeira)
        assert status == 200
        assert extract_amounts(response) == [100]

    def test_filters_by_inclusive_period(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.credit_account(account_key, 100)

        status, response = RequestGenerator.GET_account_statement(
            account_key, {"date_from": days_from_today(-1), "date_to": days_from_today(1)}
        )
        assert status == 200
        assert extract_amounts(response) == [100]

    def test_period_outside_the_entries_is_empty(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.credit_account(account_key, 100)

        status, response = RequestGenerator.GET_account_statement(
            account_key, {"date_to": days_from_today(-2)}
        )
        assert status == 200
        assert response["data"] == []

        status, response = RequestGenerator.GET_account_statement(
            account_key, {"date_from": days_from_today(2)}
        )
        assert status == 200
        assert response["data"] == []

    def test_refuses_inverted_period(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        status, response = RequestGenerator.GET_account_statement(
            account_key, {"date_from": "2026-02-01", "date_to": "2026-01-01"}
        )
        assert status == 400
        assert response["code"] == "QIT000010"

    def test_refuses_impossible_date(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        status, response = RequestGenerator.GET_account_statement(account_key, {"date_from": "2026-02-30"})
        assert status == 422
        assert response["code"] == "QIT001015"

    def test_wrong_params(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        for params in [
            {"page": -3},
            {"limit": 500},
            {"limit": 101},
            {"date_from": "01/01/2026"},
            {"date_to": "2026-1-1"},
        ]:
            status, response = RequestGenerator.GET_account_statement(account_key, params)

            assert status == 400, f"aceitou os parametros {params}"
            assert response["code"] == "QIT000001"

    def test_refuses_unknown_query_param(self):
        account_key = ObjectGenerator.create_company_account()["account_key"]

        status, response = RequestGenerator.GET_account_statement(account_key, {"data_inicio": "2026-01-01"})
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_account_not_found(self):
        """Conta que nao existe e 404, nao extrato vazio."""
        status, response = RequestGenerator.GET_account_statement(NOT_FOUND_KEY)
        assert status == 404
        assert response["code"] == "QIT001021"
