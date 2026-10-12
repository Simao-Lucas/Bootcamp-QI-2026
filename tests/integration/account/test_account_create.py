from tests.utils import ObjectGenerator, RequestGenerator


NOT_FOUND_KEY = "00000000-0000-0000-0000-000000000000"


def create_employee() -> str:
    company_key, position_key = ObjectGenerator.create_company_with_position()
    return ObjectGenerator.create_employee(company_key, position_key)["employee_key"]


class TestCompanyAccountCreate:
    def test_creates_company_account(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        status, response = RequestGenerator.POST_company_account(company_key)
        assert status == 201

        _key = response["account_key"]

        status, response = RequestGenerator.GET_account(_key)
        assert status == 200
        assert response["account_key"] == _key
        assert response["account_type"] == "company"
        assert response["company_key"] == company_key
        assert response["employee_key"] is None
        assert response["balance_amount"] == 0
        assert response["status"] == "active"

    def test_each_account_gets_its_own_key(self):
        primeira = ObjectGenerator.create_company_account()
        segunda = ObjectGenerator.create_company_account()

        assert primeira["account_key"] != segunda["account_key"]

    def test_company_not_found(self):
        status, response = RequestGenerator.POST_company_account(NOT_FOUND_KEY)
        assert status == 404
        assert response["code"] == "QIT001011"

    def test_refuses_second_account_for_the_same_company(self):
        company_key = ObjectGenerator.create_company()["company_key"]
        ObjectGenerator.create_company_account(company_key)

        status, response = RequestGenerator.POST_company_account(company_key)
        assert status == 409
        assert response["code"] == "QIT001019"


class TestEmployeeAccountCreate:
    def test_creates_employee_account(self):
        employee_key = create_employee()

        status, response = RequestGenerator.POST_employee_account(employee_key)
        assert status == 201

        _key = response["account_key"]

        status, response = RequestGenerator.GET_account(_key)
        assert status == 200
        assert response["account_key"] == _key
        assert response["account_type"] == "employee"
        assert response["employee_key"] == employee_key
        assert response["company_key"] is None
        assert response["balance_amount"] == 0
        assert response["status"] == "active"

    def test_employee_not_found(self):
        status, response = RequestGenerator.POST_employee_account(NOT_FOUND_KEY)
        assert status == 404
        assert response["code"] == "QIT001016"

    def test_refuses_second_account_for_the_same_employee(self):
        employee_key = create_employee()
        ObjectGenerator.create_employee_account(employee_key)

        status, response = RequestGenerator.POST_employee_account(employee_key)
        assert status == 409
        assert response["code"] == "QIT001020"

    def test_refuses_account_for_terminated_employee(self):
        employee_key = create_employee()
        ObjectGenerator.terminate_employee(employee_key)

        status, response = RequestGenerator.POST_employee_account(employee_key)
        assert status == 422
        assert response["code"] == "QIT001017"

    def test_company_and_employee_accounts_are_independent(self):
        company_key, position_key = ObjectGenerator.create_company_with_position()
        employee_key = ObjectGenerator.create_employee(company_key, position_key)["employee_key"]

        company_account = ObjectGenerator.create_company_account(company_key)

        status, response = RequestGenerator.POST_employee_account(employee_key)
        assert status == 201
        assert response["account_key"] != company_account["account_key"]
