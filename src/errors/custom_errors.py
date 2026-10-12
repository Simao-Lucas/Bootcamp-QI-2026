from errors import QIException


class InvalidDocumentNumber(QIException):
    code = "QIT001003"

    def __init__(self, document_number) -> None:
        title = "Invalid Document Number"
        http_status = 422
        description = f"The document number {document_number} is not a valid CPF."
        translation = "O CPF informado não é válido."
        super().__init__(title, self.code, http_status, description, translation)


class InvalidCompanyDocumentNumber(QIException):
    code = "QIT001008"

    def __init__(self, document_number) -> None:
        title = "Invalid Company Document Number"
        http_status = 422
        description = f"The document number {document_number} is not a valid CNPJ."
        translation = "O CNPJ informado não é válido."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedCompanyDocumentNumber(QIException):
    code = "QIT001009"

    def __init__(self, document_number) -> None:
        title = "Company Document Number already registered"
        http_status = 409
        description = f"There is already a company with the document number {document_number}."
        translation = "Já existe uma empresa com este CNPJ."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedCompanyEmail(QIException):
    code = "QIT001010"

    def __init__(self, email) -> None:
        title = "Company Email already registered"
        http_status = 409
        description = f"There is already a company with the email {email}."
        translation = "Já existe uma empresa com este e-mail."
        super().__init__(title, self.code, http_status, description, translation)


class NotFoundCompany(QIException):
    code = "QIT001011"

    def __init__(self, company_key) -> None:
        title = "Company not Found"
        http_status = 404
        description = f"Company with key {company_key} was not found."
        translation = f"A empresa com chave {company_key} não foi encontrada."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedPositionName(QIException):
    code = "QIT001012"

    def __init__(self, name) -> None:
        title = "Position Name already registered"
        http_status = 409
        description = f"The company already has a position named {name}."
        translation = "A empresa já tem um cargo com este nome."
        super().__init__(title, self.code, http_status, description, translation)


class NotFoundPosition(QIException):
    code = "QIT001013"

    def __init__(self, position_key) -> None:
        title = "Position not Found"
        http_status = 404
        description = f"Position with key {position_key} was not found in this company."
        translation = f"O cargo com chave {position_key} não foi encontrado nesta empresa."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedEmployeeDocumentNumber(QIException):
    code = "QIT001014"

    def __init__(self, document_number) -> None:
        title = "Employee Document Number already registered"
        http_status = 409
        description = f"The company already has an employee with the document number {document_number}."
        translation = "A empresa já tem um funcionário com este CPF."
        super().__init__(title, self.code, http_status, description, translation)


class InvalidDate(QIException):
    code = "QIT001015"

    def __init__(self, raw_date) -> None:
        title = "Invalid Date"
        http_status = 422
        description = f"The date {raw_date} is not a real date."
        translation = "A data informada não existe."
        super().__init__(title, self.code, http_status, description, translation)


class NotFoundEmployee(QIException):
    code = "QIT001016"

    def __init__(self, employee_key) -> None:
        title = "Employee not Found"
        http_status = 404
        description = f"Employee with key {employee_key} was not found."
        translation = f"O funcionário com chave {employee_key} não foi encontrado."
        super().__init__(title, self.code, http_status, description, translation)


class EmployeeAlreadyTerminated(QIException):
    code = "QIT001017"

    def __init__(self, employee_key, terminated_at) -> None:
        title = "Employee already terminated"
        http_status = 422
        description = f"Employee with key {employee_key} was terminated on {terminated_at} and cannot change."
        translation = "Este funcionário já foi desligado e não pode ser alterado."
        super().__init__(title, self.code, http_status, description, translation)


class TerminationBeforeHiring(QIException):
    code = "QIT001018"

    def __init__(self, terminated_at, hired_at) -> None:
        title = "Termination before hiring"
        http_status = 422
        description = f"The termination date {terminated_at} is before the hiring date {hired_at}."
        translation = "A data de desligamento não pode ser anterior à data de contratação."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedCompanyAccount(QIException):
    code = "QIT001019"

    def __init__(self, company_key) -> None:
        title = "Company already has an account"
        http_status = 409
        description = f"Company with key {company_key} already has an account."
        translation = "Esta empresa já tem uma conta."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedEmployeeAccount(QIException):
    code = "QIT001020"

    def __init__(self, employee_key) -> None:
        title = "Employee already has an account"
        http_status = 409
        description = f"Employee with key {employee_key} already has an account."
        translation = "Este funcionário já tem uma conta."
        super().__init__(title, self.code, http_status, description, translation)


class NotFoundAccount(QIException):
    code = "QIT001021"

    def __init__(self, account_key) -> None:
        title = "Account not Found"
        http_status = 404
        description = f"Account with key {account_key} was not found."
        translation = f"A conta com chave {account_key} não foi encontrada."
        super().__init__(title, self.code, http_status, description, translation)


class AccountClosed(QIException):
    code = "QIT001022"

    def __init__(self, account_key, new_status) -> None:
        title = "Account is closed"
        http_status = 422
        description = f"Account with key {account_key} is closed and cannot change to {new_status}."
        translation = "Esta conta está encerrada e não pode ser alterada."
        super().__init__(title, self.code, http_status, description, translation)


class AccountWithBalance(QIException):
    code = "QIT001023"

    def __init__(self, account_key, balance_amount) -> None:
        title = "Account still has balance"
        http_status = 422
        description = f"Account with key {account_key} still has a balance of {balance_amount} and cannot be closed."
        translation = "A conta ainda tem saldo e não pode ser encerrada."
        super().__init__(title, self.code, http_status, description, translation)


class AccountNotActive(QIException):
    code = "QIT001024"

    def __init__(self, account_key, status) -> None:
        title = "Account is not active"
        http_status = 422
        description = f"Account with key {account_key} is {status} and cannot move money."
        translation = "A conta não está ativa."
        super().__init__(title, self.code, http_status, description, translation)


class NotFoundTransfer(QIException):
    code = "QIT001025"

    def __init__(self, transfer_key) -> None:
        title = "Transfer not Found"
        http_status = 404
        description = f"Transfer with key {transfer_key} was not found."
        translation = f"A transferência com chave {transfer_key} não foi encontrada."
        super().__init__(title, self.code, http_status, description, translation)


class SameAccountTransfer(QIException):
    code = "QIT001026"

    def __init__(self, account_key) -> None:
        title = "Source and destination are the same account"
        http_status = 422
        description = f"Account with key {account_key} cannot transfer to itself."
        translation = "A conta de origem e a de destino são a mesma."
        super().__init__(title, self.code, http_status, description, translation)


class BankAccountAsDestination(QIException):
    code = "QIT001027"

    def __init__(self, account_key) -> None:
        title = "Bank account cannot receive transfers"
        http_status = 422
        description = f"Account with key {account_key} is the bank account and cannot be a destination."
        translation = "A conta do banco não pode ser destino de uma transferência."
        super().__init__(title, self.code, http_status, description, translation)


class InsufficientBalance(QIException):
    code = "QIT001028"

    def __init__(self, account_key, balance_amount, needed_amount) -> None:
        title = "Insufficient balance"
        http_status = 422
        description = (
            f"Account with key {account_key} has a balance of {balance_amount} "
            f"and needs {needed_amount} (amount + fee)."
        )
        translation = "A conta não tem saldo para o valor mais a taxa."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedIdempotencyKey(QIException):
    code = "QIT001029"

    def __init__(self, idempotency_key) -> None:
        title = "Idempotency key already used"
        http_status = 409
        description = f"The idempotency key {idempotency_key} was already used with a different request."
        translation = "Esta chave de idempotência já foi usada em outro pedido."
        super().__init__(title, self.code, http_status, description, translation)


class NotFoundPayroll(QIException):
    code = "QIT001030"

    def __init__(self, payroll_key) -> None:
        title = "Payroll not Found"
        http_status = 404
        description = f"Payroll with key {payroll_key} was not found."
        translation = f"A folha com chave {payroll_key} não foi encontrada."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedPayrollMonth(QIException):
    code = "QIT001031"

    def __init__(self, reference_month) -> None:
        title = "Payroll month already registered"
        http_status = 409
        description = f"The company already has a payroll for {reference_month} that is not canceled."
        translation = "A empresa já tem uma folha não cancelada neste mês."
        super().__init__(title, self.code, http_status, description, translation)


class NoActiveEmployees(QIException):
    code = "QIT001032"

    def __init__(self, company_key) -> None:
        title = "Company has no active employees"
        http_status = 422
        description = f"Company with key {company_key} has no active employees to pay."
        translation = "A empresa não tem funcionários ativos."
        super().__init__(title, self.code, http_status, description, translation)


class EmployeeWithoutActiveAccount(QIException):
    code = "QIT001033"

    def __init__(self, employee_key) -> None:
        title = "Employee without active account"
        http_status = 422
        description = f"Active employee with key {employee_key} has no active account."
        translation = "Há funcionário ativo sem conta ativa."
        super().__init__(title, self.code, http_status, description, translation)


class CalculationApiUnavailable(QIException):
    code = "QIT001034"

    def __init__(self, reason) -> None:
        title = "Calculation API unavailable"
        http_status = 502
        description = f"The salary calculation API failed: {reason}."
        translation = "A API de cálculo de salários está indisponível. Tente de novo mais tarde."
        super().__init__(title, self.code, http_status, description, translation)


class InvalidCalculationResponse(QIException):
    code = "QIT001035"

    def __init__(self, employee_key, body) -> None:
        title = "Invalid calculation response"
        http_status = 502
        description = f"The salary calculation API answered an invalid net amount for employee {employee_key}: {body}."
        translation = "A API de cálculo de salários respondeu um valor inválido."
        super().__init__(title, self.code, http_status, description, translation)


class PayrollNotPending(QIException):
    code = "QIT001036"

    def __init__(self, payroll_key, status) -> None:
        title = "Payroll is not pending"
        http_status = 422
        description = f"Payroll with key {payroll_key} is {status}, and only a pending payroll can do this."
        translation = "A folha não está pendente."
        super().__init__(title, self.code, http_status, description, translation)


class PayrollNotProcessing(QIException):
    code = "QIT001037"

    def __init__(self, payroll_key, status) -> None:
        title = "Payroll is not processing"
        http_status = 422
        description = f"Payroll with key {payroll_key} is {status}, and only a processing payroll can do this."
        translation = "A folha não está em processamento."
        super().__init__(title, self.code, http_status, description, translation)


class PayrollWithoutFailedItems(QIException):
    code = "QIT001038"

    def __init__(self, payroll_key) -> None:
        title = "Payroll has no failed items"
        http_status = 422
        description = f"Payroll with key {payroll_key} has no failed items."
        translation = "A folha não tem itens que falharam."
        super().__init__(title, self.code, http_status, description, translation)


class SettlementAccountTransfer(QIException):
    code = "QIT001039"

    def __init__(self, account_key) -> None:
        title = "Settlement account cannot transfer"
        http_status = 422
        description = f"Account with key {account_key} is a payroll settlement account and cannot be used in transfers."
        translation = "A conta de liquidação de folha não pode ser usada em transferências."
        super().__init__(title, self.code, http_status, description, translation)


class CompanyWithoutAccount(QIException):
    code = "QIT001040"

    def __init__(self, company_key) -> None:
        title = "Company has no account"
        http_status = 422
        description = f"Company with key {company_key} has no account to pay the payroll from."
        translation = "A empresa não tem conta para pagar a folha."
        super().__init__(title, self.code, http_status, description, translation)
