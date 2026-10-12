from tests.utils import ObjectGenerator, RequestGenerator


NOT_FOUND_KEY = "00000000-0000-0000-0000-000000000000"
TRANSFER_FIELDS = {
    "transfer_key",
    "source_account_key",
    "destination_account_key",
    "external_destination",
    "amount",
    "fee_amount",
    "created_at",
}
EXTERNAL_DESTINATION_FIELDS = {"bank_code", "branch_number", "account_number"}


class TestTransferGet:
    def test_gets_internal_transfer(self):
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)
        destination = ObjectGenerator.create_company_account()["account_key"]
        transfer_key = ObjectGenerator.create_transfer(source, destination, 30000)["transfer_key"]

        status, response = RequestGenerator.GET_transfer(transfer_key)
        assert status == 200
        assert response["transfer_key"] == transfer_key
        assert response["source_account_key"] == source
        assert response["destination_account_key"] == destination
        assert response["external_destination"] is None
        assert response["amount"] == 30000
        assert response["fee_amount"] == 150

    def test_gets_external_transfer(self):
        source = ObjectGenerator.create_funded_company_account(100000, fee_amount=150)
        transfer_key = ObjectGenerator.create_external_transfer(
            source, 30000, bank_code="260", branch_number="0001", account_number="98765-4"
        )["transfer_key"]

        status, response = RequestGenerator.GET_transfer(transfer_key)
        assert status == 200
        assert response["transfer_key"] == transfer_key
        assert response["source_account_key"] == source
        assert response["destination_account_key"] is None
        assert response["external_destination"] == {
            "bank_code": "260",
            "branch_number": "0001",
            "account_number": "98765-4",
        }
        assert response["amount"] == 30000
        assert response["fee_amount"] == 150

    def test_does_not_expose_internal_fields(self):
        """As contas saem pela chave, nunca pelo id do banco de dados."""
        source = ObjectGenerator.create_funded_company_account()
        destination = ObjectGenerator.create_company_account()["account_key"]

        internal_key = ObjectGenerator.create_transfer(source, destination)["transfer_key"]
        external_key = ObjectGenerator.create_external_transfer(source)["transfer_key"]

        status, response = RequestGenerator.GET_transfer(internal_key)
        assert status == 200
        assert set(response.keys()) == TRANSFER_FIELDS

        status, response = RequestGenerator.GET_transfer(external_key)
        assert status == 200
        assert set(response.keys()) == TRANSFER_FIELDS
        assert set(response["external_destination"].keys()) == EXTERNAL_DESTINATION_FIELDS

    def test_keeps_leading_zeros(self):
        source = ObjectGenerator.create_funded_company_account()
        transfer_key = ObjectGenerator.create_external_transfer(
            source, bank_code="001", branch_number="0042", account_number="0001234-5"
        )["transfer_key"]

        status, response = RequestGenerator.GET_transfer(transfer_key)
        assert status == 200
        assert response["external_destination"]["bank_code"] == "001"
        assert response["external_destination"]["branch_number"] == "0042"
        assert response["external_destination"]["account_number"] == "0001234-5"

    def test_fee_is_frozen(self):
        company_key = ObjectGenerator.create_company(fee_amount=150)["company_key"]
        source = ObjectGenerator.create_company_account(company_key)["account_key"]
        ObjectGenerator.credit_account(source, 100000)
        destination = ObjectGenerator.create_company_account()["account_key"]

        old_key = ObjectGenerator.create_transfer(source, destination)["transfer_key"]

        status, _response = RequestGenerator.PUT_company(company_key, {"fee_amount": 500})
        assert status == 202

        new_key = ObjectGenerator.create_transfer(source, destination)["transfer_key"]

        status, response = RequestGenerator.GET_transfer(old_key)
        assert response["fee_amount"] == 150

        status, response = RequestGenerator.GET_transfer(new_key)
        assert response["fee_amount"] == 500

    def test_statement_points_to_the_transfer(self):
        source = ObjectGenerator.create_funded_company_account()
        destination = ObjectGenerator.create_company_account()["account_key"]
        transfer_key = ObjectGenerator.create_transfer(source, destination, 30000)["transfer_key"]

        status, response = RequestGenerator.GET_account_statement(destination)
        assert status == 200
        assert response["data"][0]["transfer_key"] == transfer_key

        status, response = RequestGenerator.GET_transfer(response["data"][0]["transfer_key"])
        assert status == 200
        assert response["amount"] == 30000

    def test_not_found(self):
        status, response = RequestGenerator.GET_transfer(NOT_FOUND_KEY)
        assert status == 404
        assert response["code"] == "QIT001025"

    def test_account_key_is_not_found(self):
        account_key = ObjectGenerator.create_funded_company_account()

        status, response = RequestGenerator.GET_transfer(account_key)
        assert status == 404
        assert response["code"] == "QIT001025"
