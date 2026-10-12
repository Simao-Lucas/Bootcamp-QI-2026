from os import environ

from tests.utils.requisition import ClientRequisition, BaseConnectorResponse


INTERNAL_TOKEN = environ.get("INTERNAL_TOKEN", "default_token")


class RequestGenerator:
    @staticmethod
    def POST_company(company_payload: dict) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "POST",
            "/company",
            payload=company_payload,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def GET_company(company_key: str) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "GET",
            f"/company/{company_key}",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def PUT_company(company_key: str, update_payload: dict) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "PUT",
            f"/company/{company_key}",
            payload=update_payload,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def GET_companies(params: dict = None) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "GET", "/companies", headers={"INTERNAL-TOKEN": INTERNAL_TOKEN}, query_params=params
        )
        return response.response_status, response.response_json

    @staticmethod
    def POST_position(company_key: str, position_payload: dict) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "POST",
            f"/company/{company_key}/position",
            payload=position_payload,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def GET_positions(company_key: str, params: dict = None) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "GET",
            f"/company/{company_key}/positions",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
            query_params=params,
        )
        return response.response_status, response.response_json

    @staticmethod
    def POST_employee(company_key: str, employee_payload: dict) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "POST",
            f"/company/{company_key}/employee",
            payload=employee_payload,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def GET_employee(employee_key: str) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "GET",
            f"/employee/{employee_key}",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def GET_employees(company_key: str, params: dict = None) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "GET",
            f"/company/{company_key}/employees",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
            query_params=params,
        )
        return response.response_status, response.response_json

    @staticmethod
    def PUT_employee(employee_key: str, update_payload: dict) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "PUT",
            f"/employee/{employee_key}",
            payload=update_payload,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def POST_company_account(company_key: str) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "POST",
            f"/company/{company_key}/account",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def POST_employee_account(employee_key: str) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "POST",
            f"/employee/{employee_key}/account",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def GET_account(account_key: str) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "GET",
            f"/account/{account_key}",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def PUT_account(account_key: str, update_payload: dict) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "PUT",
            f"/account/{account_key}",
            payload=update_payload,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def GET_account_statement(account_key: str, params: dict = None) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "GET",
            f"/account/{account_key}/statement",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
            query_params=params,
        )
        return response.response_status, response.response_json

    @staticmethod
    def POST_test_credit(account_key: str, credit_payload: dict) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "POST",
            f"/test/account/{account_key}/credit",
            payload=credit_payload,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def POST_transfer(transfer_payload: dict) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "POST",
            "/transfer",
            payload=transfer_payload,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def POST_external_transfer(transfer_payload: dict) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "POST",
            "/transfer/external",
            payload=transfer_payload,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def GET_transfer(transfer_key: str) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "GET",
            f"/transfer/{transfer_key}",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def POST_payroll(company_key: str, payroll_payload: dict) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "POST",
            f"/company/{company_key}/payroll",
            payload=payroll_payload,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def GET_payroll(payroll_key: str) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "GET",
            f"/payroll/{payroll_key}",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def GET_payrolls(company_key: str, params: dict = None) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "GET",
            f"/company/{company_key}/payrolls",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
            query_params=params,
        )
        return response.response_status, response.response_json

    @staticmethod
    def PUT_payroll_pay(payroll_key: str) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "PUT",
            f"/payroll/{payroll_key}/pay",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def PUT_payroll_cancel(payroll_key: str) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "PUT",
            f"/payroll/{payroll_key}/cancel",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def PUT_payroll_retry(payroll_key: str) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "PUT",
            f"/payroll/{payroll_key}/retry",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def PUT_payroll_refund(payroll_key: str) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "PUT",
            f"/payroll/{payroll_key}/refund",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json

    @staticmethod
    def POST_test_payroll_process(payroll_key: str) -> BaseConnectorResponse:
        response = ClientRequisition.send(
            "POST",
            f"/test/payroll/{payroll_key}/process",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        return response.response_status, response.response_json
