from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


EMPLOYEE_FIELDS = {
    "employee_key",
    "company_key",
    "position_key",
    "name",
    "document_number",
    "email",
    "hired_at",
    "terminated_at",
}


class TestEmployeeGet:
    def test_gets_employee(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()
        payload = PayloadGenerator.create_employee_payload(position_key, name="Ana Souza")

        status, response = RequestGenerator.POST_employee(company_key, payload)
        assert status == 201
        _key = response["employee_key"]

        status, response = RequestGenerator.GET_employee(_key)
        assert status == 200
        assert response == {
            "employee_key": _key,
            "company_key": company_key,
            "position_key": position_key,
            "name": "Ana Souza",
            "document_number": payload["document_number"],
            "email": payload["email"],
            "hired_at": payload["hired_at"],
            "terminated_at": None,
        }

    def test_does_not_expose_internal_fields(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()
        employee_key = ObjectGenerator.create_employee(company_key, position_key)["employee_key"]

        status, response = RequestGenerator.GET_employee(employee_key)
        assert status == 200
        assert set(response.keys()) == EMPLOYEE_FIELDS

    def test_shows_termination_date(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()
        employee_key = ObjectGenerator.create_employee(company_key, position_key)["employee_key"]

        ObjectGenerator.terminate_employee(employee_key, terminated_at="2026-01-31")

        status, response = RequestGenerator.GET_employee(employee_key)
        assert status == 200
        assert response["terminated_at"] == "2026-01-31"

    def test_not_found(self):
        status, response = RequestGenerator.GET_employee("00000000-0000-0000-0000-000000000000")
        assert status == 404
        assert response["code"] == "QIT001016"

    def test_key_of_another_entity_is_not_found(self):
        company_key, _position_key = ObjectGenerator.create_company_with_position()

        status, response = RequestGenerator.GET_employee(company_key)
        assert status == 404
        assert response["code"] == "QIT001016"
