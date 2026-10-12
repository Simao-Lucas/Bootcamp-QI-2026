from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


class TestCompanyUpdate:
    def test_refuses_empty_body(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        status, response = RequestGenerator.PUT_company(company_key, {})
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_unknown_field(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        for campo, valor in [("name", "Outro Nome LTDA"), ("payment_day", 10)]:
            status, response = RequestGenerator.PUT_company(company_key, {"fee_amount": 200, campo: valor})

            assert status == 400, f"aceitou mudar o campo '{campo}'"
            assert response["code"] == "QIT000001"

    def test_refuses_malformed_fee_amount(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        for fee_amount in ["200", 2.5, None, 0, -1]:
            status, response = RequestGenerator.PUT_company(company_key, {"fee_amount": fee_amount})

            assert status == 400, f"aceitou a taxa {fee_amount!r}"
            assert response["code"] == "QIT000001"

    def test_changes_fee_amount(self):
        payload = PayloadGenerator.create_company_payload(fee_amount=150)
        status, response = RequestGenerator.POST_company(payload)
        assert status == 201
        company_key = response["company_key"]

        status, response = RequestGenerator.PUT_company(company_key, {"fee_amount": 275})
        assert status == 202
        assert response["company_key"] == company_key

        status, response = RequestGenerator.GET_company(company_key)
        assert status == 200
        assert response["fee_amount"] == 275

    def test_changing_fee_keeps_the_other_fields(self):
        payload = PayloadGenerator.create_company_payload()
        status, response = RequestGenerator.POST_company(payload)
        assert status == 201
        company_key = response["company_key"]

        status, _response = RequestGenerator.PUT_company(company_key, {"fee_amount": 99})
        assert status == 202

        status, response = RequestGenerator.GET_company(company_key)
        assert response["name"] == payload["name"]
        assert response["document_number"] == payload["document_number"]
        assert response["email"] == payload["email"]
        assert response["payment_day"] == payload["payment_day"]

    def test_changes_only_the_requested_company(self):
        primeira = ObjectGenerator.create_company()["company_key"]
        segunda = ObjectGenerator.create_company()["company_key"]

        status, _response = RequestGenerator.PUT_company(primeira, {"fee_amount": 500})
        assert status == 202

        status, response = RequestGenerator.GET_company(segunda)
        assert response["fee_amount"] == 150

    def test_not_found(self):
        status, response = RequestGenerator.PUT_company("00000000-0000-0000-0000-000000000000", {"fee_amount": 200})
        assert status == 404
        assert response["code"] == "QIT001011"
