from uuid import uuid4

from tests.utils import ObjectGenerator, RequestGenerator


NOT_FOUND_COMPANY_KEY = "00000000-0000-0000-0000-000000000000"


def extract_keys(response: dict) -> list:
    employee_keys = []
    for employee in response["data"]:
        employee_keys.append(employee["employee_key"])
    return employee_keys


class TestEmployees:

    def test_empty_list(self):
        company_key, _position_key = ObjectGenerator.create_company_with_position()

        status, response = RequestGenerator.GET_employees(company_key)
        assert status == 200
        assert response["data"] == []
        assert response["is_last_page"] is True

    def test_list_item_is_the_same_as_get(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()
        employee_key = ObjectGenerator.create_employee(company_key, position_key)["employee_key"]

        status, single = RequestGenerator.GET_employee(employee_key)
        assert status == 200

        status, response = RequestGenerator.GET_employees(company_key)
        assert status == 200
        assert response["data"] == [single]

    def test_lists_only_employees_of_the_company(self):
        primeira_empresa, primeiro_cargo = ObjectGenerator.create_company_with_position()
        segunda_empresa, segundo_cargo = ObjectGenerator.create_company_with_position()

        da_primeira = ObjectGenerator.create_employee(primeira_empresa, primeiro_cargo)
        da_segunda = ObjectGenerator.create_employee(segunda_empresa, segundo_cargo)

        status, response = RequestGenerator.GET_employees(primeira_empresa)
        assert status == 200
        assert extract_keys(response) == [da_primeira["employee_key"]]

        status, response = RequestGenerator.GET_employees(segunda_empresa)
        assert status == 200
        assert extract_keys(response) == [da_segunda["employee_key"]]

    def test_get_pages(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()

        for _funcionario in range(3):
            ObjectGenerator.create_employee(company_key, position_key)

        status, response = RequestGenerator.GET_employees(company_key)
        assert status == 200
        assert len(response["data"]) == 3
        assert response["is_last_page"] is True

        status, response = RequestGenerator.GET_employees(company_key, {"limit": 2})
        assert status == 200
        assert len(response["data"]) == 2
        assert response["is_last_page"] is False

        status, response = RequestGenerator.GET_employees(company_key, {"limit": 2, "page": 1})
        assert status == 200
        assert len(response["data"]) == 1
        assert response["is_last_page"] is True

    def test_lists_newest_first_and_pages_do_not_overlap(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()

        created_keys = []
        for _funcionario in range(3):
            created_keys.append(ObjectGenerator.create_employee(company_key, position_key)["employee_key"])

        created_keys.reverse()

        status, response = RequestGenerator.GET_employees(company_key, {"limit": 2})
        assert status == 200
        assert extract_keys(response) == created_keys[:2]
        assert response["is_last_page"] is False

        status, response = RequestGenerator.GET_employees(company_key, {"limit": 2, "page": 1})
        assert status == 200
        assert extract_keys(response) == created_keys[2:]
        assert response["is_last_page"] is True

    def test_filters_by_partial_name_ignoring_case(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()
        unique_surname = f"Albuquerque{uuid4().hex[:8]}"

        matching = ObjectGenerator.create_employee(company_key, position_key, name=f"Rita {unique_surname}")
        ObjectGenerator.create_employee(company_key, position_key, name="Carlos Lima")

        status, response = RequestGenerator.GET_employees(company_key, {"name": unique_surname.upper()})
        assert status == 200
        assert extract_keys(response) == [matching["employee_key"]]

    def test_filters_by_active(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()

        ativo = ObjectGenerator.create_employee(company_key, position_key)["employee_key"]
        desligado = ObjectGenerator.create_employee(company_key, position_key)["employee_key"]
        ObjectGenerator.terminate_employee(desligado)

        status, response = RequestGenerator.GET_employees(company_key, {"active": "true"})
        assert status == 200
        assert extract_keys(response) == [ativo]

        status, response = RequestGenerator.GET_employees(company_key, {"active": "false"})
        assert status == 200
        assert extract_keys(response) == [desligado]

        status, response = RequestGenerator.GET_employees(company_key)
        assert status == 200
        assert sorted(extract_keys(response)) == sorted([ativo, desligado])

    def test_combines_filters_with_and(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()
        shared_name = f"Mendes{uuid4().hex[:8]}"

        ativo = ObjectGenerator.create_employee(company_key, position_key, name=shared_name)["employee_key"]
        desligado = ObjectGenerator.create_employee(company_key, position_key, name=shared_name)["employee_key"]
        ObjectGenerator.terminate_employee(desligado)

        status, response = RequestGenerator.GET_employees(company_key, {"name": shared_name, "active": "true"})
        assert status == 200
        assert extract_keys(response) == [ativo]

    def test_company_not_found(self):
        status, response = RequestGenerator.GET_employees(NOT_FOUND_COMPANY_KEY)
        assert status == 404
        assert response["code"] == "QIT001011"

    def test_wrong_params(self):
        company_key, _position_key = ObjectGenerator.create_company_with_position()

        for params in [
            {"page": -3},
            {"limit": 500},
            {"limit": 101},
            {"name": ""},
            {"active": "sim"},
            {"active": "True"},
        ]:
            status, response = RequestGenerator.GET_employees(company_key, params)

            assert status == 400, f"aceitou os parametros {params}"
            assert response["code"] == "QIT000001"

    def test_refuses_unknown_query_param(self):
        company_key, _position_key = ObjectGenerator.create_company_with_position()

        status, response = RequestGenerator.GET_employees(company_key, {"ativo": "true"})
        assert status == 400
        assert response["code"] == "QIT000001"
