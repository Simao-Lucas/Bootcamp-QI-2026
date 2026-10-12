from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


NOT_FOUND_KEY = "00000000-0000-0000-0000-000000000000"


class TestEmployeeCreate:
    def test_refuses_empty_body(self):
        company_key, _position_key = ObjectGenerator.create_company_with_position()

        status, response = RequestGenerator.POST_employee(company_key, {})
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_refuses_missing_field(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()

        for campo in ["name", "document_number", "email", "hired_at", "position_key"]:
            payload = PayloadGenerator.create_employee_payload(position_key)
            del payload[campo]

            status, response = RequestGenerator.POST_employee(company_key, payload)

            assert status == 400, f"aceitou o funcionario sem o campo '{campo}'"
            assert response["code"] == "QIT000001"

    def test_schema_refuses_unknown_field(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()

        payload = PayloadGenerator.create_employee_payload(position_key)
        payload["birthdate"] = "1990-05-17"

        status, response = RequestGenerator.POST_employee(company_key, payload)
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_malformed_fields(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()

        campos_tortos = [
            ("name", ""),
            ("email", "isto-nao-e-um-email"),
            ("document_number", "52998224725"),
            ("document_number", "11.222.333/0001-81"),
            ("hired_at", "01/03/2024"),
            ("hired_at", "2024-3-1"),
            ("position_key", 123),
        ]

        for campo, valor_torto in campos_tortos:
            payload = PayloadGenerator.create_employee_payload(position_key)
            payload[campo] = valor_torto

            status, response = RequestGenerator.POST_employee(company_key, payload)

            assert status == 400, f"o campo '{campo}' aceitou o valor {valor_torto!r}"
            assert response["code"] == "QIT000001"

    def test_creates_employee(self):
        """O funcionario nasce ativo, na empresa e no cargo pedidos."""
        company_key, position_key = ObjectGenerator.create_company_with_position()
        payload = PayloadGenerator.create_employee_payload(position_key)

        status, response = RequestGenerator.POST_employee(company_key, payload)
        assert status == 201

        _key = response["employee_key"]

        status, response = RequestGenerator.GET_employee(_key)
        assert status == 200
        assert response["employee_key"] == _key
        assert response["company_key"] == company_key
        assert response["position_key"] == position_key
        assert response["name"] == payload["name"]
        assert response["document_number"] == payload["document_number"]
        assert response["email"] == payload["email"]
        assert response["hired_at"] == payload["hired_at"]
        assert response["terminated_at"] is None

    def test_each_employee_gets_its_own_key(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()

        primeiro = ObjectGenerator.create_employee(company_key, position_key)
        segundo = ObjectGenerator.create_employee(company_key, position_key)

        assert primeiro["employee_key"] != segundo["employee_key"]

    def test_company_not_found(self):
        _company_key, position_key = ObjectGenerator.create_company_with_position()
        payload = PayloadGenerator.create_employee_payload(position_key)

        status, response = RequestGenerator.POST_employee(NOT_FOUND_KEY, payload)
        assert status == 404
        assert response["code"] == "QIT001011"

    def test_position_not_found(self):
        company_key, _position_key = ObjectGenerator.create_company_with_position()
        payload = PayloadGenerator.create_employee_payload(NOT_FOUND_KEY)

        status, response = RequestGenerator.POST_employee(company_key, payload)
        assert status == 404
        assert response["code"] == "QIT001013"

    def test_position_of_another_company_is_not_found(self):
        company_key, _position_key = ObjectGenerator.create_company_with_position()
        _other_company_key, other_position_key = ObjectGenerator.create_company_with_position()

        payload = PayloadGenerator.create_employee_payload(other_position_key)

        status, response = RequestGenerator.POST_employee(company_key, payload)
        assert status == 404
        assert response["code"] == "QIT001013"

    def test_refuses_invalid_document_number(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()

        for document_number in ["111.222.333-44", "111.111.111-11"]:
            payload = PayloadGenerator.create_employee_payload(position_key, document_number=document_number)

            status, response = RequestGenerator.POST_employee(company_key, payload)

            assert status == 422, f"aceitou o CPF {document_number}"
            assert response["code"] == "QIT001003"

    def test_refuses_impossible_hired_at(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()
        payload = PayloadGenerator.create_employee_payload(position_key, hired_at="2025-02-30")

        status, response = RequestGenerator.POST_employee(company_key, payload)
        assert status == 422
        assert response["code"] == "QIT001015"

    def test_refuses_duplicated_document_number_in_the_same_company(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()

        primeiro = PayloadGenerator.create_employee_payload(position_key)
        status, _response = RequestGenerator.POST_employee(company_key, primeiro)
        assert status == 201

        segundo = PayloadGenerator.create_employee_payload(
            position_key, document_number=primeiro["document_number"]
        )

        status, response = RequestGenerator.POST_employee(company_key, segundo)
        assert status == 409
        assert response["code"] == "QIT001014"

    def test_same_document_number_is_allowed_in_another_company(self):
        primeira_empresa, primeiro_cargo = ObjectGenerator.create_company_with_position()
        segunda_empresa, segundo_cargo = ObjectGenerator.create_company_with_position()

        primeiro = PayloadGenerator.create_employee_payload(primeiro_cargo)
        status, _response = RequestGenerator.POST_employee(primeira_empresa, primeiro)
        assert status == 201

        segundo = PayloadGenerator.create_employee_payload(
            segundo_cargo, document_number=primeiro["document_number"]
        )

        status, _response = RequestGenerator.POST_employee(segunda_empresa, segundo)
        assert status == 201
