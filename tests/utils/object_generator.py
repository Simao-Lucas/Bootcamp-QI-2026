from tests.utils.mock_server import MockServerUtils
from tests.utils.requisition import BaseConnectorResponse
from tests.utils.payload_generator import PayloadGenerator
from tests.utils.request_generator import RequestGenerator


class ObjectGenerator:
    @staticmethod
    def create_company(fee_amount: int = None) -> BaseConnectorResponse:

        company_payload = PayloadGenerator.create_company_payload(fee_amount=fee_amount)

        status, response = RequestGenerator.POST_company(company_payload)
        assert status == 201

        return response

    @staticmethod
    def create_position(company_key: str, name: str = None, salary_amount: int = None) -> BaseConnectorResponse:

        position_payload = PayloadGenerator.create_position_payload(name=name, salary_amount=salary_amount)

        status, response = RequestGenerator.POST_position(company_key, position_payload)
        assert status == 201

        return response

    @staticmethod
    def create_company_with_position() -> tuple:
        """Empresa e cargo, o minimo que um funcionario precisa pra existir."""

        company_key = ObjectGenerator.create_company()["company_key"]
        position_key = ObjectGenerator.create_position(company_key)["position_key"]

        return company_key, position_key

    @staticmethod
    def create_employee(
        company_key: str, position_key: str, name: str = None, hired_at: str = None
    ) -> BaseConnectorResponse:

        employee_payload = PayloadGenerator.create_employee_payload(
            position_key, name=name, hired_at=hired_at
        )

        status, response = RequestGenerator.POST_employee(company_key, employee_payload)
        assert status == 201

        return response

    @staticmethod
    def terminate_employee(employee_key: str, terminated_at: str = "2026-01-31") -> BaseConnectorResponse:

        status, response = RequestGenerator.PUT_employee(employee_key, {"terminated_at": terminated_at})
        assert status == 202

        return response

    @staticmethod
    def create_company_account(company_key: str = None) -> BaseConnectorResponse:
        """A conta de uma empresa. Sem empresa informada, cria uma nova."""

        if company_key is None:
            company_key = ObjectGenerator.create_company()["company_key"]

        status, response = RequestGenerator.POST_company_account(company_key)
        assert status == 201

        return response

    @staticmethod
    def create_employee_account(employee_key: str = None) -> BaseConnectorResponse:
        """A conta de um funcionario. Sem funcionario informado, cria empresa, cargo e funcionario."""

        if employee_key is None:
            company_key, position_key = ObjectGenerator.create_company_with_position()
            employee_key = ObjectGenerator.create_employee(company_key, position_key)["employee_key"]

        status, response = RequestGenerator.POST_employee_account(employee_key)
        assert status == 201

        return response

    @staticmethod
    def credit_account(account_key: str, amount: int = None) -> BaseConnectorResponse:

        credit_payload = PayloadGenerator.create_credit_payload(amount)

        status, response = RequestGenerator.POST_test_credit(account_key, credit_payload)
        assert status == 201

        return response

    @staticmethod
    def update_account_status(account_key: str, new_status: str) -> BaseConnectorResponse:

        status_payload = PayloadGenerator.create_account_status_payload(new_status)

        status, response = RequestGenerator.PUT_account(account_key, status_payload)
        assert status == 202

        return response

    @staticmethod
    def create_funded_company_account(amount: int = 100000, fee_amount: int = None) -> str:
        """A conta de uma empresa nova, ja com saldo. Devolve a chave da conta.

        A taxa da empresa e o que a conta paga em cada transferencia que
        envia; sem taxa informada, vale a do cadastro padrao (150).
        """

        company_key = ObjectGenerator.create_company(fee_amount=fee_amount)["company_key"]
        account_key = ObjectGenerator.create_company_account(company_key)["account_key"]
        ObjectGenerator.credit_account(account_key, amount)

        return account_key

    @staticmethod
    def create_transfer(
        source_account_key: str, destination_account_key: str, amount: int = None
    ) -> BaseConnectorResponse:

        transfer_payload = PayloadGenerator.create_transfer_payload(
            source_account_key, destination_account_key, amount=amount
        )

        status, response = RequestGenerator.POST_transfer(transfer_payload)
        assert status == 201

        return response

    @staticmethod
    def create_external_transfer(
        source_account_key: str,
        amount: int = None,
        bank_code: str = None,
        branch_number: str = None,
        account_number: str = None,
    ) -> BaseConnectorResponse:

        transfer_payload = PayloadGenerator.create_external_transfer_payload(
            source_account_key,
            amount=amount,
            bank_code=bank_code,
            branch_number=branch_number,
            account_number=account_number,
        )

        status, response = RequestGenerator.POST_external_transfer(transfer_payload)
        assert status == 201

        return response

    @staticmethod
    def create_payroll_scenario(
        net_amounts: list = None,
        salary_amount: int = 450000,
        fee_amount: int = 150,
        company_balance: int = None,
    ) -> dict:
        """Tudo que uma folha precisa para ser gerada e paga.

        Uma empresa com conta, um cargo e um funcionario com conta para
        cada valor em `net_amounts`, com o MockServer ja respondendo esse
        valor como o calculo de cada um. Sem saldo informado, a conta da
        empresa recebe exatamente o total mais as taxas.
        """
        if net_amounts is None:
            net_amounts = [400000, 380000]

        if company_balance is None:
            company_balance = sum(net_amounts) + fee_amount * len(net_amounts)

        company_key = ObjectGenerator.create_company(fee_amount=fee_amount)["company_key"]
        company_account_key = ObjectGenerator.create_company_account(company_key)["account_key"]
        if company_balance > 0:
            ObjectGenerator.credit_account(company_account_key, company_balance)

        position_key = ObjectGenerator.create_position(company_key, salary_amount=salary_amount)["position_key"]

        employees = []
        for net_amount in net_amounts:
            employee_key = ObjectGenerator.create_employee(company_key, position_key)["employee_key"]
            account_key = ObjectGenerator.create_employee_account(employee_key)["account_key"]
            MockServerUtils.expect_net_amount(employee_key, net_amount)

            employees.append({"employee_key": employee_key, "account_key": account_key, "net_amount": net_amount})

        return {
            "company_key": company_key,
            "company_account_key": company_account_key,
            "position_key": position_key,
            "fee_amount": fee_amount,
            "employees": employees,
        }

    @staticmethod
    def create_payroll(company_key: str, reference_month: str = None) -> BaseConnectorResponse:

        payroll_payload = PayloadGenerator.create_payroll_payload(reference_month)

        status, response = RequestGenerator.POST_payroll(company_key, payroll_payload)
        assert status == 201

        return response

    @staticmethod
    def pay_payroll(payroll_key: str) -> BaseConnectorResponse:

        status, response = RequestGenerator.PUT_payroll_pay(payroll_key)
        assert status == 202

        return response

    @staticmethod
    def process_payroll(payroll_key: str) -> BaseConnectorResponse:

        status, response = RequestGenerator.POST_test_payroll_process(payroll_key)
        assert status == 200

        return response

    @staticmethod
    def cancel_payroll(payroll_key: str) -> BaseConnectorResponse:

        status, response = RequestGenerator.PUT_payroll_cancel(payroll_key)
        assert status == 202

        return response

    @staticmethod
    def create_processing_payroll(scenario: dict = None) -> dict:
        """Uma folha ja paga pela empresa, com o dinheiro na liquidacao, esperando o worker."""

        if scenario is None:
            scenario = ObjectGenerator.create_payroll_scenario()

        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]
        ObjectGenerator.pay_payroll(payroll_key)

        status, payroll = RequestGenerator.GET_payroll(payroll_key)
        assert status == 200

        return payroll
