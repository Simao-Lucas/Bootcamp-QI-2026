from tests.utils import ObjectGenerator, RequestGenerator


NOT_FOUND_KEY = "00000000-0000-0000-0000-000000000000"


def create_employee(hired_at: str = "2024-03-01") -> tuple:
    company_key, position_key = ObjectGenerator.create_company_with_position()
    employee_key = ObjectGenerator.create_employee(company_key, position_key, hired_at=hired_at)["employee_key"]

    return company_key, position_key, employee_key


class TestEmployeeUpdate:
    def test_refuses_empty_body(self):
        _company_key, _position_key, employee_key = create_employee()

        status, response = RequestGenerator.PUT_employee(employee_key, {})
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_unknown_field(self):
        _company_key, _position_key, employee_key = create_employee()

        for campo, valor in [("name", "Outro Nome"), ("hired_at", "2020-01-01")]:
            status, response = RequestGenerator.PUT_employee(employee_key, {campo: valor})

            assert status == 400, f"aceitou mudar o campo '{campo}'"
            assert response["code"] == "QIT000001"

    def test_schema_refuses_malformed_fields(self):
        _company_key, _position_key, employee_key = create_employee()

        campos_tortos = [
            ("terminated_at", "31/01/2026"),
            ("terminated_at", "2026-1-31"),
            ("position_key", 123),
        ]

        for campo, valor_torto in campos_tortos:
            status, response = RequestGenerator.PUT_employee(employee_key, {campo: valor_torto})

            assert status == 400, f"o campo '{campo}' aceitou o valor {valor_torto!r}"
            assert response["code"] == "QIT000001"

    def test_changes_position(self):
        company_key, _position_key, employee_key = create_employee()
        new_position_key = ObjectGenerator.create_position(company_key, name="Supervisor")["position_key"]

        status, response = RequestGenerator.PUT_employee(employee_key, {"position_key": new_position_key})
        assert status == 202
        assert response["employee_key"] == employee_key

        status, response = RequestGenerator.GET_employee(employee_key)
        assert status == 200
        assert response["position_key"] == new_position_key
        assert response["terminated_at"] is None

    def test_terminates_employee(self):
        _company_key, position_key, employee_key = create_employee()

        status, response = RequestGenerator.PUT_employee(employee_key, {"terminated_at": "2026-01-31"})
        assert status == 202
        assert response["employee_key"] == employee_key

        status, response = RequestGenerator.GET_employee(employee_key)
        assert status == 200
        assert response["terminated_at"] == "2026-01-31"
        assert response["position_key"] == position_key

    def test_changes_position_and_terminates_at_once(self):
        company_key, _position_key, employee_key = create_employee()
        new_position_key = ObjectGenerator.create_position(company_key, name="Supervisor")["position_key"]

        status, _response = RequestGenerator.PUT_employee(
            employee_key, {"position_key": new_position_key, "terminated_at": "2026-01-31"}
        )
        assert status == 202

        status, response = RequestGenerator.GET_employee(employee_key)
        assert status == 200
        assert response["position_key"] == new_position_key
        assert response["terminated_at"] == "2026-01-31"

    def test_employee_not_found(self):
        status, response = RequestGenerator.PUT_employee(NOT_FOUND_KEY, {"terminated_at": "2026-01-31"})
        assert status == 404
        assert response["code"] == "QIT001016"

    def test_position_not_found(self):
        _company_key, _position_key, employee_key = create_employee()

        status, response = RequestGenerator.PUT_employee(employee_key, {"position_key": NOT_FOUND_KEY})
        assert status == 404
        assert response["code"] == "QIT001013"

    def test_position_of_another_company_is_not_found(self):
        _company_key, _position_key, employee_key = create_employee()
        _other_company_key, other_position_key = ObjectGenerator.create_company_with_position()

        status, response = RequestGenerator.PUT_employee(employee_key, {"position_key": other_position_key})
        assert status == 404
        assert response["code"] == "QIT001013"

        status, response = RequestGenerator.GET_employee(employee_key)
        assert response["position_key"] != other_position_key

    def test_terminated_employee_cannot_change(self):
        company_key, _position_key, employee_key = create_employee()
        new_position_key = ObjectGenerator.create_position(company_key, name="Supervisor")["position_key"]
        ObjectGenerator.terminate_employee(employee_key, terminated_at="2026-01-31")

        for payload in [{"position_key": new_position_key}, {"terminated_at": "2026-02-28"}]:
            status, response = RequestGenerator.PUT_employee(employee_key, payload)

            assert status == 422, f"mudou um funcionario desligado com {payload}"
            assert response["code"] == "QIT001017"

        status, response = RequestGenerator.GET_employee(employee_key)
        assert response["terminated_at"] == "2026-01-31"
        assert response["position_key"] != new_position_key

    def test_refuses_termination_before_hiring(self):
        _company_key, _position_key, employee_key = create_employee(hired_at="2024-03-01")

        status, response = RequestGenerator.PUT_employee(employee_key, {"terminated_at": "2024-02-29"})
        assert status == 422
        assert response["code"] == "QIT001018"

        status, response = RequestGenerator.GET_employee(employee_key)
        assert response["terminated_at"] is None

    def test_accepts_termination_on_hiring_day(self):
        _company_key, _position_key, employee_key = create_employee(hired_at="2024-03-01")

        status, _response = RequestGenerator.PUT_employee(employee_key, {"terminated_at": "2024-03-01"})
        assert status == 202

    def test_refuses_impossible_termination_date(self):
        _company_key, _position_key, employee_key = create_employee()

        status, response = RequestGenerator.PUT_employee(employee_key, {"terminated_at": "2026-02-30"})
        assert status == 422
        assert response["code"] == "QIT001015"
