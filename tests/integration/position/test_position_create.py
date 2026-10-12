from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


NOT_FOUND_COMPANY_KEY = "00000000-0000-0000-0000-000000000000"


class TestPositionCreate:
    def test_refuses_empty_body(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        status, response = RequestGenerator.POST_position(company_key, {})
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_refuses_missing_field(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        for campo in ["name", "salary_amount"]:
            payload = PayloadGenerator.create_position_payload()
            del payload[campo]

            status, response = RequestGenerator.POST_position(company_key, payload)

            assert status == 400, f"aceitou o cargo sem o campo '{campo}'"
            assert response["code"] == "QIT000001"

    def test_schema_refuses_unknown_field(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        payload = PayloadGenerator.create_position_payload()
        payload["campo_que_nao_existe"] = 1

        status, response = RequestGenerator.POST_position(company_key, payload)
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_malformed_fields(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        campos_tortos = [
            ("name", ""),
            ("name", None),
            ("salary_amount", "450000"),
            ("salary_amount", 4500.5),
            ("salary_amount", None),
            ("salary_amount", 0),
            ("salary_amount", -100),
        ]

        for campo, valor_torto in campos_tortos:
            payload = PayloadGenerator.create_position_payload()
            payload[campo] = valor_torto

            status, response = RequestGenerator.POST_position(company_key, payload)

            assert status == 400, f"o campo '{campo}' aceitou o valor {valor_torto!r}"
            assert response["code"] == "QIT000001"

    def test_accepts_minimum_salary(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        payload = PayloadGenerator.create_position_payload(salary_amount=1)

        status, _response = RequestGenerator.POST_position(company_key, payload)
        assert status == 201

    def test_creates_position(self):
        company_key = ObjectGenerator.create_company()["company_key"]
        payload = PayloadGenerator.create_position_payload()

        status, response = RequestGenerator.POST_position(company_key, payload)
        assert status == 201

        _key = response["position_key"]

        status, response = RequestGenerator.GET_positions(company_key)
        assert status == 200
        assert len(response["data"]) == 1

        position = response["data"][0]
        assert position["position_key"] == _key
        assert position["name"] == payload["name"]
        assert position["salary_amount"] == payload["salary_amount"]

    def test_each_position_gets_its_own_key(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        primeiro = ObjectGenerator.create_position(company_key, name="Caixa")
        segundo = ObjectGenerator.create_position(company_key, name="Padeiro")

        assert primeiro["position_key"] != segundo["position_key"]

    def test_company_not_found(self):
        payload = PayloadGenerator.create_position_payload()

        status, response = RequestGenerator.POST_position(NOT_FOUND_COMPANY_KEY, payload)
        assert status == 404
        assert response["code"] == "QIT001011"

    def test_refuses_duplicated_name_in_the_same_company(self):
        company_key = ObjectGenerator.create_company()["company_key"]
        ObjectGenerator.create_position(company_key, name="Gerente")

        payload = PayloadGenerator.create_position_payload(name="Gerente", salary_amount=900000)

        status, response = RequestGenerator.POST_position(company_key, payload)
        assert status == 409
        assert response["code"] == "QIT001012"

    def test_same_name_is_allowed_in_another_company(self):
        primeira_empresa = ObjectGenerator.create_company()["company_key"]
        segunda_empresa = ObjectGenerator.create_company()["company_key"]

        ObjectGenerator.create_position(primeira_empresa, name="Gerente")

        payload = PayloadGenerator.create_position_payload(name="Gerente")

        status, _response = RequestGenerator.POST_position(segunda_empresa, payload)
        assert status == 201
