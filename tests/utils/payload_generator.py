from uuid import uuid4

from tests.utils.random_generator import RandomGenerator


class PayloadGenerator:
    @staticmethod
    def create_company_payload(
        name: str = None,
        document_number: str = None,
        email: str = None,
        payment_day: int = None,
        fee_amount: int = None,
    ) -> dict:
        """Uma empresa valida, com qualquer campo trocado a pedido.

        CNPJ e e-mail saem aleatorios porque precisam ser unicos: duas
        empresas seguidas nao podem bater na regra de duplicidade. A taxa
        vai em centavos: 150 sao R$ 1,50 por transferencia.
        """
        if name is None:
            name = "Padaria do Joao LTDA"

        if document_number is None:
            document_number = RandomGenerator.generate_cnpj()

        if email is None:
            email = f"financeiro.{uuid4()}@padaria.com.br"

        if payment_day is None:
            payment_day = 5

        if fee_amount is None:
            fee_amount = 150

        payload = {
            "name": name,
            "document_number": document_number,
            "email": email,
            "payment_day": payment_day,
            "fee_amount": fee_amount,
        }
        return payload

    @staticmethod
    def create_position_payload(name: str = None, salary_amount: int = None) -> dict:
        """Um cargo valido, com qualquer campo trocado a pedido.

        O salario vai em centavos: 450000 sao R$ 4.500,00. O nome e fixo
        porque so precisa ser unico dentro da mesma empresa, e cada
        teste cria a propria empresa.
        """
        if name is None:
            name = "Analista Financeiro"

        if salary_amount is None:
            salary_amount = 450000

        payload = {
            "name": name,
            "salary_amount": salary_amount,
        }
        return payload

    @staticmethod
    def create_employee_payload(
        position_key: str,
        name: str = None,
        document_number: str = None,
        email: str = None,
        hired_at: str = None,
    ) -> dict:
        """Um funcionario valido, com qualquer campo trocado a pedido.

        O cargo e obrigatorio porque precisa existir antes: quem chama
        cria a empresa e o cargo, e passa a chave aqui. O CPF sai
        aleatorio porque e unico dentro da empresa.
        """
        if name is None:
            name = "Joao Pereira"

        if document_number is None:
            document_number = RandomGenerator.generate_cpf()

        if email is None:
            email = f"joao.pereira.{uuid4()}@exemplo.com.br"

        if hired_at is None:
            hired_at = "2024-03-01"

        payload = {
            "name": name,
            "document_number": document_number,
            "email": email,
            "hired_at": hired_at,
            "position_key": position_key,
        }
        return payload

    @staticmethod
    def create_credit_payload(amount: int = None) -> dict:
        """Um credito de teste. Em centavos: 100000 sao R$ 1.000,00."""
        if amount is None:
            amount = 100000

        payload = {"amount": amount}
        return payload

    @staticmethod
    def create_account_status_payload(status: str = None) -> dict:
        payload = {"status": status}
        return payload

    @staticmethod
    def create_transfer_payload(
        source_account_key: str,
        destination_account_key: str,
        amount: int = None,
        idempotency_key: str = None,
    ) -> dict:
        """Uma transferencia valida entre duas contas do sistema.

        O valor vai em centavos: 10000 sao R$ 100,00. A chave de
        idempotencia sai aleatoria, entao cada payload novo e um pedido
        novo. Quem testa retentativa manda o MESMO payload duas vezes.
        """
        if amount is None:
            amount = 10000

        if idempotency_key is None:
            idempotency_key = str(uuid4())

        payload = {
            "source_account_key": source_account_key,
            "destination_account_key": destination_account_key,
            "amount": amount,
            "idempotency_key": idempotency_key,
        }
        return payload

    @staticmethod
    def create_external_transfer_payload(
        source_account_key: str,
        amount: int = None,
        idempotency_key: str = None,
        bank_code: str = None,
        branch_number: str = None,
        account_number: str = None,
    ) -> dict:
        """Uma transferencia valida para uma conta de outro banco.

        O destino e so a identificacao bancaria: banco, agencia e conta.
        Tudo em texto, porque zero a esquerda faz parte do numero.
        """
        if amount is None:
            amount = 10000

        if idempotency_key is None:
            idempotency_key = str(uuid4())

        if bank_code is None:
            bank_code = "341"

        if branch_number is None:
            branch_number = "0123"

        if account_number is None:
            account_number = "12345-6"

        payload = {
            "source_account_key": source_account_key,
            "amount": amount,
            "idempotency_key": idempotency_key,
            "destination": {
                "bank_code": bank_code,
                "branch_number": branch_number,
                "account_number": account_number,
            },
        }
        return payload

    @staticmethod
    def create_payroll_payload(reference_month: str = None) -> dict:
        """A folha de um mes. Cada teste cria a propria empresa, entao o mes pode ser fixo."""
        if reference_month is None:
            reference_month = "2026-09"

        payload = {"reference_month": reference_month}
        return payload
