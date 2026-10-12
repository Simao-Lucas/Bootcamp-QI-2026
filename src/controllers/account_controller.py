from datetime import date

from controllers.base_controller import BaseController
from dtos import AccountDTO, AccountEntryDTO
from errors import (
    AccountClosed,
    AccountNotActive,
    AccountWithBalance,
    DuplicatedCompanyAccount,
    DuplicatedEmployeeAccount,
    EmployeeAlreadyTerminated,
    InvalidDate,
    InvalidParameter,
    NotFoundAccount,
    NotFoundCompany,
    NotFoundEmployee,
)
from models import Account, AccountEntry, AccountStatus, AccountType
from repositories import AccountRepository, CompanyRepository, EmployeeRepository


class AccountController(BaseController):

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.company_repository = CompanyRepository(self.context)
        self.employee_repository = EmployeeRepository(self.context)

    def create_company_account(self, company_key: str) -> dict:
        self.logger.debug(f"Abrindo a conta da empresa {company_key}")

        company = self.company_repository.get_by_key(company_key)

        if company is None:
            raise NotFoundCompany(company_key)

        if self.account_repository.get_by_company(company) is not None:
            raise DuplicatedCompanyAccount(company_key)

        account = self.account_repository.create(AccountType.COMPANY, company=company)

        account_dto = AccountDTO.only_obj_key(account)
        self.session.commit()

        return account_dto

    def create_employee_account(self, employee_key: str) -> dict:
        self.logger.debug(f"Abrindo a conta do funcionário {employee_key}")

        employee = self.employee_repository.get_by_key(employee_key)

        if employee is None:
            raise NotFoundEmployee(employee_key)

        if employee.terminated_at is not None:
            raise EmployeeAlreadyTerminated(employee_key, employee.terminated_at)

        if self.account_repository.get_by_employee(employee) is not None:
            raise DuplicatedEmployeeAccount(employee_key)

        account = self.account_repository.create(AccountType.EMPLOYEE, employee=employee)

        account_dto = AccountDTO.only_obj_key(account)
        self.session.commit()

        return account_dto

    def get_by_key(self, account_key: str) -> dict:
        self.logger.debug(f"Buscando a conta de chave {account_key}")

        account = self._get_account(account_key)

        return AccountDTO.obj_to_dict(account)

    def update_status(self, account_key: str, new_status: str) -> dict:
        account = self._get_account_for_update(account_key)

        if account.status.enumerator == AccountStatus.CLOSED:
            raise AccountClosed(account_key, new_status)

        if new_status == AccountStatus.CLOSED and account.balance_amount > 0:
            raise AccountWithBalance(account_key, account.balance_amount)

        self.account_repository.update_status(account, new_status)

        account_dto = AccountDTO.only_obj_key(account)
        self.session.commit()

        return account_dto

    def credit_for_test(self, account_key: str, amount: int) -> dict:
        self.logger.debug(f"Creditando {amount} na conta {account_key}")

        account = self._get_account_for_update(account_key)

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        self.account_repository.add_entry(account, AccountEntry.TEST_CREDIT, AccountEntry.CREDIT, amount)

        account_dto = AccountDTO.balance(account)
        self.session.commit()

        return account_dto

    def get_statement(self, account_key: str, limit: int, offset: int, filters: dict) -> dict:
        account = self._get_account(account_key)

        date_from = filters.get("date_from")
        date_to = filters.get("date_to")

        if date_from is not None:
            date_from = self._parse_date(date_from)
            filters["date_from"] = date_from

        if date_to is not None:
            date_to = self._parse_date(date_to)
            filters["date_to"] = date_to

        if date_from is not None and date_to is not None:
            if date_from > date_to:
                raise InvalidParameter(f"date_from ({date_from}) is after date_to ({date_to})")

        entries_list = self.account_repository.list_entries_page(account, limit, offset, filters)

        # Pedimos um a mais que o limite só pra saber se existe próxima
        # página. Se veio o extra, ele não entra na resposta.
        is_last_page = True
        if len(entries_list) > limit:
            is_last_page = False
            entries_list = entries_list[:-1]

        return {
            "entries_list_dto": AccountEntryDTO.list_obj_to_list_dict(entries_list),
            "is_last_page": is_last_page,
        }

    def _get_account(self, account_key: str) -> Account:
        account = self.account_repository.get_by_key(account_key)

        if account is None:
            raise NotFoundAccount(account_key)

        return account

    def _get_account_for_update(self, account_key: str) -> Account:
        account = self.account_repository.get_by_key_for_update(account_key)

        if account is None:
            raise NotFoundAccount(account_key)

        return account

    def _parse_date(self, raw_date: str) -> date:
        try:
            return date.fromisoformat(raw_date)
        except ValueError:
            raise InvalidDate(raw_date)
