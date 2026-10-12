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


class TestTransferExternal:
    def test_refuses_empty_body(self):
        status, response = RequestGenerator.POST_external_transfer({})
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_unknown_field(self):
        source = ObjectGenerator.create_funded_company_account()

        payload = PayloadGenerator.create_external_transfer_payload(source)
        payload["fee_amount"] = 0

        status, response = RequestGenerator.POST_external_transfer(payload)
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_destination_account_key(self):
        source = ObjectGenerator.create_funded_company_account()
        destination = ObjectGenerator.create_company_account()["account_key"]

        payload = PayloadGenerator.create_external_transfer_payload(source)
        payload["destination_account_key"] = destination

        status, response = RequestGenerator.POST_external_transfer(payload)
        assert status == 400
        assert response["code"] == "QIT000001"

        assert balance(destination) == 0

    def test_schema_refuses_unknown_field_in_destination(self):
        source = ObjectGenerator.create_funded_company_account()

        for field, value in [("name", "Maria Silva"), ("document_number", "12345678909")]:
            payload = PayloadGenerator.create_external_transfer_payload(source)
            payload["destination"][field] = value

            status, response = RequestGenerator.POST_external_transfer(payload)

            assert status == 400, f"aceitou o campo {field} no destino"
            assert response["code"] == "QIT000001"

    def test_schema_refuses_missing_field(self):
        source = ObjectGenerator.create_funded_company_account()

        for field in ["source_account_key", "amount", "idempotency_key", "destination"]:
            payload = PayloadGenerator.create_external_transfer_payload(source)
            del payload[field]

            status, response = RequestGenerator.POST_external_transfer(payload)

            assert status == 400, f"aceitou sem o campo {field}"
            assert response["code"] == "QIT000001"

        assert balance(source) == 100000

    def test_schema_refuses_missing_destination_field(self):
        source = ObjectGenerator.create_funded_company_account()

        for field in ["bank_code", "branch_number", "account_number"]:
            payload = PayloadGenerator.create_external_transfer_payload(source)
            del payload["destination"][field]

            status, response = RequestGenerator.POST_external_transfer(payload)

            assert status == 400, f"aceitou o destino sem {field}"
            assert response["code"] == "QIT000001"

        assert balance(source) == 100000

    def test_schema_refuses_malformed_amount(self):
        source = ObjectGenerator.create_funded_company_account()

        for amount in ["10000", 100.5, None, 0, -100]:
            payload = PayloadGenerator.create_external_transfer_payload(source)
            payload["amount"] = amount

            status, response = RequestGenerator.POST_external_transfer(payload)

            assert status == 400, f"aceitou o valor {amount!r}"
            assert response["code"] == "QIT000001"

    def test_schema_refuses_malformed_bank_code(self):
        source = ObjectGenerator.create_funded_company_account()

        for bank_code in ["34", "3411", "abc", 341, ""]:
            payload = PayloadGenerator.create_external_transfer_payload(source)
            payload["destination"]["bank_code"] = bank_code

            status, response = RequestGenerator.POST_external_transfer(payload)

            assert status == 400, f"aceitou o banco {bank_code!r}"
            assert response["code"] == "QIT000001"

    def test_schema_refuses_malformed_branch_number(self):
        source = ObjectGenerator.create_funded_company_account()

        for branch_number in ["123", "12345", "abcd", 123, ""]:
            payload = PayloadGenerator.create_external_transfer_payload(source)
            payload["destination"]["branch_number"] = branch_number

            status, response = RequestGenerator.POST_external_transfer(payload)

            assert status == 400, f"aceitou a agencia {branch_number!r}"
            assert response["code"] == "QIT000001"

    def test_schema_refuses_malformed_account_number(self):
        source = ObjectGenerator.create_funded_company_account()

        for account_number in ["", 123456, "abcde-f", None]:
            payload = PayloadGenerator.create_external_transfer_payload(source)
            payload["destination"]["account_number"] = account_number

            status, response = RequestGenerator.POST_external_transfer(payload)

            assert status == 400, f"aceitou a conta {account_number!r}"
            assert response["code"] == "QIT000001"

    def test_transfers_to_external_bank(self):
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)

        status, response = RequestGenerator.POST_external_transfer(
            PayloadGenerator.create_external_transfer_payload(source, 30000)
        )
        assert status == 201
        assert "transfer_key" in response
        assert response["fee_amount"] == 150

        assert balance(source) == 69850

    def test_amount_leaves_the_system(self):
        bank = DbUtils.bank_account_key()
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)

        bank_before = balance(bank)
        ObjectGenerator.create_external_transfer(source, 30000)

        assert balance(bank) == bank_before + 150

    def test_uses_fee_of_source_company(self):
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=300)

        response = ObjectGenerator.create_external_transfer(source, 10000)
        assert response["fee_amount"] == 300

        assert balance(source) == 89700

    def test_employee_account_pays_employer_fee(self):
        company_key = ObjectGenerator.create_company(fee_amount=275)["company_key"]
        position_key = ObjectGenerator.create_position(company_key)["position_key"]
        employee_key = ObjectGenerator.create_employee(company_key, position_key)["employee_key"]
        source = ObjectGenerator.create_employee_account(employee_key)["account_key"]
        ObjectGenerator.credit_account(source, 50000)

        response = ObjectGenerator.create_external_transfer(source, 10000)
        assert response["fee_amount"] == 275

        assert balance(source) == 39725

    def test_transfers_whole_balance(self):
        source = ObjectGenerator.create_funded_company_account(10150, fee_amount=150)

        status, _response = RequestGenerator.POST_external_transfer(
            PayloadGenerator.create_external_transfer_payload(source, 10000)
        )
        assert status == 201

        assert balance(source) == 0

    def test_accepts_minimum_amount(self):
        source = ObjectGenerator.create_funded_company_account(1000, fee_amount=150)

        status, _response = RequestGenerator.POST_external_transfer(
            PayloadGenerator.create_external_transfer_payload(source, 1)
        )
        assert status == 201

        assert balance(source) == 849

    def test_writes_statement_entries(self):
        bank = DbUtils.bank_account_key()
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)

        transfer_key = ObjectGenerator.create_external_transfer(source, 30000)["transfer_key"]

        source_entries = entries_of_transfer(source, transfer_key)
        movements = sorted((e["origin"], e["entry_type"], e["amount"]) for e in source_entries)
        assert movements == [("fee", "debit", 150), ("transfer", "debit", 30000)]

        status, response = RequestGenerator.GET_account_statement(source)
        assert response["data"][0]["balance_after"] == 69850

        bank_entries = entries_of_transfer(bank, transfer_key)
        assert len(bank_entries) == 1
        assert bank_entries[0]["origin"] == "fee"
        assert bank_entries[0]["entry_type"] == "credit"
        assert bank_entries[0]["amount"] == 150

    def test_retry_with_same_body_returns_original(self):
        bank = DbUtils.bank_account_key()
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)
        payload = PayloadGenerator.create_external_transfer_payload(source, 10000)

        status, first = RequestGenerator.POST_external_transfer(payload)
        assert status == 201
        bank_after_first = balance(bank)

        status, second = RequestGenerator.POST_external_transfer(payload)
        assert status == 200
        assert second["transfer_key"] == first["transfer_key"]
        assert second["fee_amount"] == first["fee_amount"]

        assert balance(source) == 89850
        assert balance(bank) == bank_after_first

    def test_reused_key_with_different_destination(self):
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)
        payload = PayloadGenerator.create_external_transfer_payload(
            source, 10000, account_number="12345-6"
        )

        status, _response = RequestGenerator.POST_external_transfer(payload)
        assert status == 201

        payload["destination"]["account_number"] = "12345-7"
        status, response = RequestGenerator.POST_external_transfer(payload)
        assert status == 409
        assert response["code"] == "QIT001029"

        assert balance(source) == 89850

    def test_reused_key_of_internal_transfer(self):

        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]

        internal_payload = PayloadGenerator.create_transfer_payload(source, destination, 10000)
        status, _response = RequestGenerator.POST_transfer(internal_payload)
        assert status == 201

        external_payload = PayloadGenerator.create_external_transfer_payload(
            source, 10000, idempotency_key=internal_payload["idempotency_key"]
        )
        status, response = RequestGenerator.POST_external_transfer(external_payload)
        assert status == 409
        assert response["code"] == "QIT001029"

        assert balance(source) == 89850

    def test_source_not_found(self):
        status, response = RequestGenerator.POST_external_transfer(
            PayloadGenerator.create_external_transfer_payload(NOT_FOUND_KEY)
        )
        assert status == 404
        assert response["code"] == "QIT001021"

    def test_refuses_insufficient_balance(self):
        bank = DbUtils.bank_account_key()
        source = ObjectGenerator.create_funded_company_account(10149, fee_amount=150)

        bank_before = balance(bank)
        status, response = RequestGenerator.POST_external_transfer(
            PayloadGenerator.create_external_transfer_payload(source, 10000)
        )
        assert status == 422
        assert response["code"] == "QIT001028"

        assert balance(source) == 10149
        assert balance(bank) == bank_before

        status, response = RequestGenerator.GET_account_statement(source)
        assert len(response["data"]) == 1

    def test_refuses_blocked_source(self):
        source = ObjectGenerator.create_funded_company_account()
        ObjectGenerator.update_account_status(source, "blocked")

        status, response = RequestGenerator.POST_external_transfer(
            PayloadGenerator.create_external_transfer_payload(source)
        )
        assert status == 422
        assert response["code"] == "QIT001024"

        assert balance(source) == 100000

    def test_refuses_closed_source(self):
        source = ObjectGenerator.create_company_account()["account_key"]
        ObjectGenerator.update_account_status(source, "closed")

        status, response = RequestGenerator.POST_external_transfer(
            PayloadGenerator.create_external_transfer_payload(source)
        )
        assert status == 422
        assert response["code"] == "QIT001024"

    def test_refuses_settlement_account_as_source(self):
        settlement = ObjectGenerator.create_processing_payroll()["settlement_account_key"]

        status, response = RequestGenerator.POST_external_transfer(
            PayloadGenerator.create_external_transfer_payload(settlement, amount=100)
        )
        assert status == 422
        assert response["code"] == "QIT001039"

        assert balance(settlement) == 780300

    def test_concurrent_transfers_never_overdraw(self):
        source = ObjectGenerator.create_funded_company_account(10150, fee_amount=150)
        payloads = [PayloadGenerator.create_external_transfer_payload(source, 10000) for _ in range(5)]

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(RequestGenerator.POST_external_transfer, payloads))

        statuses = sorted(status for status, _response in results)
        assert statuses == [201, 422, 422, 422, 422]

        assert balance(source) == 0
