from concurrent.futures import ThreadPoolExecutor

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


NOT_FOUND_KEY = "00000000-0000-0000-0000-000000000000"


def balance(account_key: str) -> int:
    status, response = RequestGenerator.GET_account(account_key)
    assert status == 200
    return response["balance_amount"]


def entries_of_transfer(account_key: str, transfer_key: str) -> list:
    status, response = RequestGenerator.GET_account_statement(account_key, {"limit": 100})
    assert status == 200

    entries = []
    for entry in response["data"]:
        if entry["transfer_key"] == transfer_key:
            entries.append(entry)
    return entries


class TestTransferCreate:

    def test_refuses_empty_body(self):
        status, response = RequestGenerator.POST_transfer({})
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_unknown_field(self):
        source = ObjectGenerator.create_funded_company_account()
        destination = ObjectGenerator.create_company_account()["account_key"]

        payload = PayloadGenerator.create_transfer_payload(source, destination)
        payload["fee_amount"] = 0

        status, response = RequestGenerator.POST_transfer(payload)
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_missing_field(self):
        source = ObjectGenerator.create_funded_company_account()
        destination = ObjectGenerator.create_company_account()["account_key"]

        for field in ["source_account_key", "destination_account_key", "amount", "idempotency_key"]:
            payload = PayloadGenerator.create_transfer_payload(source, destination)
            del payload[field]

            status, response = RequestGenerator.POST_transfer(payload)

            assert status == 400, f"aceitou sem o campo {field}"
            assert response["code"] == "QIT000001"

        assert balance(source) == 100000

    def test_schema_refuses_malformed_amount(self):
        source = ObjectGenerator.create_funded_company_account()
        destination = ObjectGenerator.create_company_account()["account_key"]

        for amount in ["10000", 100.5, None, 0, -100]:
            payload = PayloadGenerator.create_transfer_payload(source, destination)
            payload["amount"] = amount

            status, response = RequestGenerator.POST_transfer(payload)

            assert status == 400, f"aceitou o valor {amount!r}"
            assert response["code"] == "QIT000001"

    def test_schema_refuses_malformed_idempotency_key(self):
        source = ObjectGenerator.create_funded_company_account()
        destination = ObjectGenerator.create_company_account()["account_key"]

        for idempotency_key in ["", None, 123]:
            payload = PayloadGenerator.create_transfer_payload(source, destination)
            payload["idempotency_key"] = idempotency_key

            status, response = RequestGenerator.POST_transfer(payload)

            assert status == 400, f"aceitou a chave {idempotency_key!r}"
            assert response["code"] == "QIT000001"

    def test_transfers_between_accounts(self):
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)
        destination = ObjectGenerator.create_employee_account()["account_key"]

        status, response = RequestGenerator.POST_transfer(
            PayloadGenerator.create_transfer_payload(source, destination, 30000)
        )
        assert status == 201
        assert "transfer_key" in response
        assert response["fee_amount"] == 150

        assert balance(source) == 69850
        assert balance(destination) == 30000

    def test_fee_goes_to_bank_account(self):
        bank = DbUtils.bank_account_key()
        source = ObjectGenerator.create_funded_company_account(fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]

        bank_before = balance(bank)
        ObjectGenerator.create_transfer(source, destination, 10000)

        assert balance(bank) == bank_before + 150

    def test_money_only_changes_place(self):
        bank = DbUtils.bank_account_key()
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]

        total_before = balance(source) + balance(destination) + balance(bank)
        ObjectGenerator.create_transfer(source, destination, 25000)

        assert balance(source) + balance(destination) + balance(bank) == total_before

    def test_uses_fee_of_source_company(self):
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=300)
        destination_company = ObjectGenerator.create_company(fee_amount=999)["company_key"]
        destination = ObjectGenerator.create_company_account(destination_company)["account_key"]

        response = ObjectGenerator.create_transfer(source, destination, 10000)
        assert response["fee_amount"] == 300

        assert balance(source) == 89700

    def test_employee_account_pays_employer_fee(self):
        company_key = ObjectGenerator.create_company(fee_amount=275)["company_key"]
        position_key = ObjectGenerator.create_position(company_key)["position_key"]
        employee_key = ObjectGenerator.create_employee(company_key, position_key)["employee_key"]
        source = ObjectGenerator.create_employee_account(employee_key)["account_key"]
        ObjectGenerator.credit_account(source, 50000)

        destination = ObjectGenerator.create_company_account()["account_key"]

        response = ObjectGenerator.create_transfer(source, destination, 10000)
        assert response["fee_amount"] == 275

        assert balance(source) == 39725

    def test_transfers_whole_balance(self):
        source = ObjectGenerator.create_funded_company_account(10150, fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]

        status, _response = RequestGenerator.POST_transfer(
            PayloadGenerator.create_transfer_payload(source, destination, 10000)
        )
        assert status == 201

        assert balance(source) == 0
        assert balance(destination) == 10000

    def test_accepts_minimum_amount(self):
        source = ObjectGenerator.create_funded_company_account(1000, fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]

        status, _response = RequestGenerator.POST_transfer(
            PayloadGenerator.create_transfer_payload(source, destination, 1)
        )
        assert status == 201

        assert balance(source) == 849
        assert balance(destination) == 1

    def test_writes_statement_entries(self):
        bank = DbUtils.bank_account_key()
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]

        transfer_key = ObjectGenerator.create_transfer(source, destination, 30000)["transfer_key"]

        source_entries = entries_of_transfer(source, transfer_key)
        movements = sorted((e["origin"], e["entry_type"], e["amount"]) for e in source_entries)
        assert movements == [("fee", "debit", 150), ("transfer", "debit", 30000)]

        status, response = RequestGenerator.GET_account_statement(source)
        assert response["data"][0]["balance_after"] == 69850

        destination_entries = entries_of_transfer(destination, transfer_key)
        assert len(destination_entries) == 1
        assert destination_entries[0]["origin"] == "transfer"
        assert destination_entries[0]["entry_type"] == "credit"
        assert destination_entries[0]["amount"] == 30000
        assert destination_entries[0]["balance_after"] == 30000

        bank_entries = entries_of_transfer(bank, transfer_key)
        assert len(bank_entries) == 1
        assert bank_entries[0]["origin"] == "fee"
        assert bank_entries[0]["entry_type"] == "credit"
        assert bank_entries[0]["amount"] == 150

    def test_retry_with_same_body_returns_original(self):
        bank = DbUtils.bank_account_key()
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]
        payload = PayloadGenerator.create_transfer_payload(source, destination, 10000)

        status, first = RequestGenerator.POST_transfer(payload)
        assert status == 201
        bank_after_first = balance(bank)

        status, second = RequestGenerator.POST_transfer(payload)
        assert status == 200
        assert second["transfer_key"] == first["transfer_key"]
        assert second["fee_amount"] == first["fee_amount"]

        assert balance(source) == 89850
        assert balance(destination) == 10000
        assert balance(bank) == bank_after_first

    def test_retry_after_balance_spent_still_returns_original(self):
        source = ObjectGenerator.create_funded_company_account(10150, fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]
        payload = PayloadGenerator.create_transfer_payload(source, destination, 10000)

        status, first = RequestGenerator.POST_transfer(payload)
        assert status == 201

        status, second = RequestGenerator.POST_transfer(payload)
        assert status == 200
        assert second["transfer_key"] == first["transfer_key"]

    def test_refused_request_does_not_take_the_key(self):
        source = ObjectGenerator.create_funded_company_account(100, fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]
        payload = PayloadGenerator.create_transfer_payload(source, destination, 10000)

        status, response = RequestGenerator.POST_transfer(payload)
        assert status == 422
        assert response["code"] == "QIT001028"

        ObjectGenerator.credit_account(source, 10050)

        status, _response = RequestGenerator.POST_transfer(payload)
        assert status == 201
        assert balance(source) == 0

    def test_reused_key_with_different_amount(self):
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]
        payload = PayloadGenerator.create_transfer_payload(source, destination, 10000)

        status, _response = RequestGenerator.POST_transfer(payload)
        assert status == 201

        payload["amount"] = 20000
        status, response = RequestGenerator.POST_transfer(payload)
        assert status == 409
        assert response["code"] == "QIT001029"

        assert balance(source) == 89850
        assert balance(destination) == 10000

    def test_reused_key_with_different_destination(self):
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]
        other_destination = ObjectGenerator.create_company_account()["account_key"]
        payload = PayloadGenerator.create_transfer_payload(source, destination, 10000)

        status, _response = RequestGenerator.POST_transfer(payload)
        assert status == 201

        payload["destination_account_key"] = other_destination
        status, response = RequestGenerator.POST_transfer(payload)
        assert status == 409
        assert response["code"] == "QIT001029"

        assert balance(other_destination) == 0

    def test_key_is_unique_across_accounts(self):
        destination = ObjectGenerator.create_company_account()["account_key"]
        first_source = ObjectGenerator.create_funded_company_account()
        second_source = ObjectGenerator.create_funded_company_account()

        payload = PayloadGenerator.create_transfer_payload(first_source, destination, 10000)
        status, _response = RequestGenerator.POST_transfer(payload)
        assert status == 201

        payload["source_account_key"] = second_source
        status, response = RequestGenerator.POST_transfer(payload)
        assert status == 409
        assert response["code"] == "QIT001029"

        assert balance(second_source) == 100000

    def test_source_not_found(self):
        destination = ObjectGenerator.create_company_account()["account_key"]

        status, response = RequestGenerator.POST_transfer(
            PayloadGenerator.create_transfer_payload(NOT_FOUND_KEY, destination)
        )
        assert status == 404
        assert response["code"] == "QIT001021"

        assert balance(destination) == 0

    def test_destination_not_found(self):
        source = ObjectGenerator.create_funded_company_account()

        status, response = RequestGenerator.POST_transfer(
            PayloadGenerator.create_transfer_payload(source, NOT_FOUND_KEY)
        )
        assert status == 404
        assert response["code"] == "QIT001021"

        assert balance(source) == 100000

    def test_refuses_same_account(self):
        source = ObjectGenerator.create_funded_company_account()

        status, response = RequestGenerator.POST_transfer(
            PayloadGenerator.create_transfer_payload(source, source)
        )
        assert status == 422
        assert response["code"] == "QIT001026"

        assert balance(source) == 100000

    def test_refuses_bank_account_as_destination(self):
        bank = DbUtils.bank_account_key()
        source = ObjectGenerator.create_funded_company_account()

        bank_before = balance(bank)
        status, response = RequestGenerator.POST_transfer(
            PayloadGenerator.create_transfer_payload(source, bank)
        )
        assert status == 422
        assert response["code"] == "QIT001027"

        assert balance(source) == 100000
        assert balance(bank) == bank_before

    def test_refuses_settlement_account_as_source(self):
        settlement = ObjectGenerator.create_processing_payroll()["settlement_account_key"]
        destination = ObjectGenerator.create_company_account()["account_key"]

        status, response = RequestGenerator.POST_transfer(
            PayloadGenerator.create_transfer_payload(settlement, destination, amount=100)
        )
        assert status == 422
        assert response["code"] == "QIT001039"

        assert balance(settlement) == 780300
        assert balance(destination) == 0

    def test_refuses_settlement_account_as_destination(self):
        settlement = ObjectGenerator.create_processing_payroll()["settlement_account_key"]
        source = ObjectGenerator.create_funded_company_account()

        status, response = RequestGenerator.POST_transfer(
            PayloadGenerator.create_transfer_payload(source, settlement)
        )
        assert status == 422
        assert response["code"] == "QIT001039"

        assert balance(source) == 100000
        assert balance(settlement) == 780300

    def test_refuses_insufficient_balance(self):
        bank = DbUtils.bank_account_key()
        source = ObjectGenerator.create_funded_company_account(10149, fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]

        bank_before = balance(bank)
        status, response = RequestGenerator.POST_transfer(
            PayloadGenerator.create_transfer_payload(source, destination, 10000)
        )
        assert status == 422
        assert response["code"] == "QIT001028"

        assert balance(source) == 10149
        assert balance(destination) == 0
        assert balance(bank) == bank_before

        status, response = RequestGenerator.GET_account_statement(source)
        assert len(response["data"]) == 1

    def test_refuses_blocked_source(self):
        source = ObjectGenerator.create_funded_company_account()
        destination = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.update_account_status(source, "blocked")

        status, response = RequestGenerator.POST_transfer(
            PayloadGenerator.create_transfer_payload(source, destination)
        )
        assert status == 422
        assert response["code"] == "QIT001024"

        assert balance(source) == 100000

    def test_refuses_blocked_destination(self):
        source = ObjectGenerator.create_funded_company_account()
        destination = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.update_account_status(destination, "blocked")

        status, response = RequestGenerator.POST_transfer(
            PayloadGenerator.create_transfer_payload(source, destination)
        )
        assert status == 422
        assert response["code"] == "QIT001024"

        assert balance(source) == 100000

    def test_refuses_closed_destination(self):
        source = ObjectGenerator.create_funded_company_account()
        destination = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.update_account_status(destination, "closed")

        status, response = RequestGenerator.POST_transfer(
            PayloadGenerator.create_transfer_payload(source, destination)
        )
        assert status == 422
        assert response["code"] == "QIT001024"

        assert balance(source) == 100000
        assert balance(destination) == 0

    def test_concurrent_transfers_never_overdraw(self):
        source = ObjectGenerator.create_funded_company_account(10150, fee_amount=150)
        destinations = [ObjectGenerator.create_company_account()["account_key"] for _ in range(5)]
        payloads = [
            PayloadGenerator.create_transfer_payload(source, destination, 10000)
            for destination in destinations
        ]

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(RequestGenerator.POST_transfer, payloads))

        statuses = sorted(status for status, _response in results)
        assert statuses == [201, 422, 422, 422, 422]

        assert balance(source) == 0
        assert sum(balance(destination) for destination in destinations) == 10000

    def test_concurrent_retries_charge_once(self):
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]
        payload = PayloadGenerator.create_transfer_payload(source, destination, 10000)

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(RequestGenerator.POST_transfer, [payload] * 5))

        statuses = [status for status, _response in results]
        assert statuses.count(201) == 1
        assert set(statuses) <= {200, 201, 409}

        assert balance(source) == 89850
        assert balance(destination) == 10000
