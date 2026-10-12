from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator
from tests.utils.requisition import ClientRequisition


COMPANY_FIELDS = {"company_key", "name", "document_number", "email", "payment_day", "fee_amount"}


class TestCompanyGet:
    def test_gets_company(self):
        payload = PayloadGenerator.create_company_payload()
        status, response = RequestGenerator.POST_company(payload)
        assert status == 201

        _key = response["company_key"]

        status, response = RequestGenerator.GET_company(_key)
        assert status == 200
        assert response["company_key"] == _key
        assert response["name"] == payload["name"]
        assert response["document_number"] == payload["document_number"]
        assert response["email"] == payload["email"]
        assert response["payment_day"] == payload["payment_day"]
        assert response["fee_amount"] == payload["fee_amount"]

    def test_does_not_expose_internal_fields(self):
        status, response = RequestGenerator.POST_company(PayloadGenerator.create_company_payload())
        assert status == 201

        status, response = RequestGenerator.GET_company(response["company_key"])
        assert status == 200
        assert set(response.keys()) == COMPANY_FIELDS

    def test_not_found(self):
        status, response = RequestGenerator.GET_company("00000000-0000-0000-0000-000000000000")
        assert status == 404
        assert response["code"] == "QIT001011"

    def test_key_of_another_entity_is_not_found(self):
        company = ObjectGenerator.create_company()
        position = ObjectGenerator.create_position(company["company_key"])

        status, response = RequestGenerator.GET_company(position["position_key"])
        assert status == 404
        assert response["code"] == "QIT001011"

    def test_requires_internal_token(self):
        status, response = RequestGenerator.POST_company(PayloadGenerator.create_company_payload())
        assert status == 201

        response = ClientRequisition.send("GET", f"/company/{response['company_key']}")
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000002"
