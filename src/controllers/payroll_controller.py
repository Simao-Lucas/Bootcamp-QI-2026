from datetime import date
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from connectors import CalculationConnector
from constants import PAYROLL_BATCH_SIZE
from controllers.base_controller import BaseController
from dtos import PayrollDTO
from errors import (
    AccountNotActive,
    CalculationApiUnavailable,
    CompanyWithoutAccount,
    DuplicatedPayrollMonth,
    EmployeeWithoutActiveAccount,
    InsufficientBalance,
    InvalidCalculationResponse,
    NoActiveEmployees,
    NotFoundCompany,
    NotFoundPayroll,
    PayrollNotPending,
    PayrollNotProcessing,
    PayrollWithoutFailedItems,
)
from models import (
    Account,
    AccountEntry,
    AccountStatus,
    AccountType,
    Company,
    Employee,
    Payroll,
    PayrollItemStatus,
    PayrollStatus,
    Transfer,
)
from repositories import (
    AccountRepository,
    CompanyRepository,
    EmployeeRepository,
    PayrollRepository,
    TransferRepository,
)


class PayrollController(BaseController):
    def __init__(self) -> None:
        super().__init__(__name__)
        self.company_repository = CompanyRepository(self.context)
        self.employee_repository = EmployeeRepository(self.context)
        self.account_repository = AccountRepository(self.context)
        self.transfer_repository = TransferRepository(self.context)
        self.payroll_repository = PayrollRepository(self.context)
        self.calculation_connector = CalculationConnector()

    def create(self, company_key: str, payroll_data: dict) -> dict:
        raw_month = payroll_data["reference_month"]

        self.logger.debug(f"Gerando a folha de {raw_month} da empresa {company_key}")

        company = self._get_company(company_key)
        reference_month = self._parse_month(raw_month)

        if self.payroll_repository.get_not_canceled_by_company_and_month(company, reference_month) is not None:
            raise DuplicatedPayrollMonth(raw_month)

        employees = self.employee_repository.list_active_by_company(company)

        if not employees:
            raise NoActiveEmployees(company_key)

        for employee in employees:
            self._check_employee_account(employee)

        calculations = []
        for employee in employees:
            gross_amount = employee.position.salary_amount
            net_amount = self._calculate_net_amount(employee, raw_month, gross_amount)
            calculations.append((employee, gross_amount, net_amount))

        payroll = self.payroll_repository.create(company, reference_month)
        for employee, gross_amount, net_amount in calculations:
            self.payroll_repository.add_item(payroll, employee, gross_amount, net_amount, company.fee_amount)

        payroll_key = payroll.payroll_key
        self._commit_new_payroll(company, reference_month, raw_month)

        return PayrollDTO.obj_to_dict(self.payroll_repository.get_by_key(payroll_key))

    def get_by_key(self, payroll_key: str) -> dict:
        self.logger.debug(f"Buscando a folha de chave {payroll_key}")

        payroll = self.payroll_repository.get_by_key(payroll_key)

        if payroll is None:
            raise NotFoundPayroll(payroll_key)

        return PayrollDTO.obj_to_dict(payroll)

    def get_list(self, company_key: str, limit: int, offset: int, filters: dict) -> dict:
        company = self._get_company(company_key)

        payrolls_list = self.payroll_repository.list_page_by_company(company, limit, offset, filters)

        is_last_page = True
        if len(payrolls_list) > limit:
            is_last_page = False
            payrolls_list = payrolls_list[:-1]

        return {
            "payrolls_list_dto": PayrollDTO.list_obj_to_list_dict(payrolls_list),
            "is_last_page": is_last_page,
        }

    def pay(self, payroll_key: str) -> dict:
        self.logger.debug(f"Pagando a folha de chave {payroll_key}")

        payroll = self._get_payroll_for_update(payroll_key)
        self._check_status(payroll, PayrollStatus.PENDING)

        company_account = self.account_repository.get_by_company(payroll.company)
        if company_account is None:
            raise CompanyWithoutAccount(payroll.company.company_key)

        self.account_repository.lock_by_ids([company_account.id])
        self._check_active(company_account)

        needed_amount = payroll.total_amount + payroll.total_fee_amount
        if company_account.balance_amount < needed_amount:
            raise InsufficientBalance(company_account.account_key, company_account.balance_amount, needed_amount)

        settlement = self.account_repository.create(AccountType.SETTLEMENT)
        self.session.flush()

        transfer = self.transfer_repository.create(
            company_account, settlement, needed_amount, 0, str(uuid4()), payroll=payroll
        )
        self._move_money(transfer, company_account, settlement, None)

        self.payroll_repository.set_settlement_account(payroll, settlement)
        self.payroll_repository.update_status(payroll, PayrollStatus.PROCESSING)

        self.session.commit()

        return {"payroll_key": payroll_key, "status": PayrollStatus.PROCESSING}

    def process(self, payroll_key: str) -> dict:
        self.logger.debug(f"Processando a folha de chave {payroll_key}")

        if self.payroll_repository.get_by_key(payroll_key) is None:
            raise NotFoundPayroll(payroll_key)

        while self._pay_next_batch(payroll_key):
            pass

        payroll = self.payroll_repository.get_by_key(payroll_key)
        items_count = self.payroll_repository.count_items_by_status(payroll)

        return {
            "payroll_key": payroll_key,
            "status": payroll.status.enumerator,
            "paid_items_count": items_count.get(PayrollItemStatus.PAID, 0),
            "failed_items_count": items_count.get(PayrollItemStatus.FAILED, 0),
        }

    def retry(self, payroll_key: str) -> dict:
        self.logger.debug(f"Devolvendo para a fila os itens que falharam na folha {payroll_key}")

        payroll = self._get_payroll_for_update(payroll_key)
        self._check_status(payroll, PayrollStatus.PROCESSING)
        failed_items = self._lock_failed_items(payroll)

        for item in failed_items:
            self.payroll_repository.update_item_status(item, PayrollItemStatus.PENDING)

        self.session.commit()

        return {"payroll_key": payroll_key, "retried_items_count": len(failed_items)}

    def refund(self, payroll_key: str) -> dict:
        self.logger.debug(f"Devolvendo para a empresa os itens que falharam na folha {payroll_key}")

        payroll = self._get_payroll_for_update(payroll_key)
        self._check_status(payroll, PayrollStatus.PROCESSING)
        failed_items = self._lock_failed_items(payroll)

        company_account = self.account_repository.get_by_company(payroll.company)
        settlement = payroll.settlement_account
        self.account_repository.lock_by_ids(sorted([company_account.id, settlement.id]))
        self._check_active(company_account)

        refunded_amount = 0
        for item in failed_items:
            amount = item.net_amount + item.fee_amount

            transfer = self.transfer_repository.create(
                settlement, company_account, amount, 0, str(uuid4()), payroll_item=item
            )
            self._move_money(transfer, settlement, company_account, None)
            self.payroll_repository.update_item_status(item, PayrollItemStatus.REFUNDED, item.failure_reason)

            refunded_amount = refunded_amount + amount

        self._finish_if_done(payroll)
        self.session.commit()

        return {"payroll_key": payroll_key, "refunded_amount": refunded_amount}

    def cancel(self, payroll_key: str) -> dict:
        self.logger.debug(f"Cancelando a folha de chave {payroll_key}")

        payroll = self._get_payroll_for_update(payroll_key)
        self._check_status(payroll, PayrollStatus.PENDING)

        self.payroll_repository.update_status(payroll, PayrollStatus.CANCELED)
        self.session.commit()

        return {"payroll_key": payroll_key}

    def pay_next_batch(self) -> str:
        payroll = self.payroll_repository.lock_next_to_pay()

        if payroll is None:
            self.session.rollback()
            return None

        payroll_key = payroll.payroll_key

        if not self._pay_batch(payroll):
            return None

        return payroll_key

    def _pay_next_batch(self, payroll_key: str) -> bool:
        payroll = self.payroll_repository.get_by_key_for_update(payroll_key)

        if payroll.status.enumerator != PayrollStatus.PROCESSING:
            self.session.rollback()
            return False

        return self._pay_batch(payroll)

    def _pay_batch(self, payroll: Payroll) -> bool:
        items = self.payroll_repository.lock_items_by_status(payroll, PayrollItemStatus.PENDING, PAYROLL_BATCH_SIZE)

        if not items:
            self.session.rollback()
            return False

        settlement = payroll.settlement_account
        bank = self.account_repository.get_bank_account()

        employee_accounts = dict()
        for account in self.account_repository.list_by_employee_ids([item.employee_id for item in items]):
            employee_accounts[account.employee_id] = account

        account_ids = {settlement.id, bank.id}
        for account in employee_accounts.values():
            account_ids.add(account.id)
        self.account_repository.lock_by_ids(sorted(account_ids))

        failed_count = 0
        for item in items:
            account = employee_accounts.get(item.employee_id)

            if account is None or account.status.enumerator != AccountStatus.ACTIVE:
                self.payroll_repository.update_item_status(
                    item, PayrollItemStatus.FAILED, self._failure_reason(account)
                )
                failed_count = failed_count + 1
                continue

            transfer = self.transfer_repository.create(
                settlement, account, item.net_amount, item.fee_amount, str(uuid4()), payroll_item=item
            )
            self._move_money(transfer, settlement, account, bank)
            self.payroll_repository.update_item_status(item, PayrollItemStatus.PAID)

        payroll_key = payroll.payroll_key
        self._finish_if_done(payroll)
        self.session.commit()

        self.logger.info(
            f"Lote da folha {payroll_key}: {len(items) - failed_count} itens pagos, {failed_count} falharam"
        )

        return True

    def _finish_if_done(self, payroll: Payroll) -> None:
        self.session.flush()
        items_count = self.payroll_repository.count_items_by_status(payroll)

        if items_count.get(PayrollItemStatus.PENDING, 0) > 0 or items_count.get(PayrollItemStatus.FAILED, 0) > 0:
            return

        self.payroll_repository.finish(payroll)
        self.account_repository.update_status(payroll.settlement_account, AccountStatus.CLOSED)

    def _get_company(self, company_key: str) -> Company:
        company = self.company_repository.get_by_key(company_key)

        if company is None:
            raise NotFoundCompany(company_key)

        return company

    def _get_payroll_for_update(self, payroll_key: str) -> Payroll:
        payroll = self.payroll_repository.get_by_key_for_update(payroll_key)

        if payroll is None:
            raise NotFoundPayroll(payroll_key)

        return payroll

    def _parse_month(self, raw_month: str) -> date:
        year, month = raw_month.split("-")

        return date(int(year), int(month), 1)

    def _check_status(self, payroll: Payroll, expected_status: str) -> None:
        status = payroll.status.enumerator

        if status == expected_status:
            return

        if expected_status == PayrollStatus.PENDING:
            raise PayrollNotPending(payroll.payroll_key, status)

        raise PayrollNotProcessing(payroll.payroll_key, status)

    def _check_employee_account(self, employee: Employee) -> None:
        account = self.account_repository.get_by_employee(employee)

        if account is None or account.status.enumerator != AccountStatus.ACTIVE:
            raise EmployeeWithoutActiveAccount(employee.employee_key)

    def _check_active(self, account: Account) -> None:
        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account.account_key, account.status.enumerator)

    def _lock_failed_items(self, payroll: Payroll) -> list:
        failed_items = self.payroll_repository.lock_items_by_status(payroll, PayrollItemStatus.FAILED)

        if not failed_items:
            raise PayrollWithoutFailedItems(payroll.payroll_key)

        return failed_items

    def _calculate_net_amount(self, employee: Employee, raw_month: str, gross_amount: int) -> int:
        response = self.calculation_connector.calculate_salary(employee.employee_key, raw_month, gross_amount)

        if response.status != 200:
            raise CalculationApiUnavailable(f"status {response.status}")

        net_amount = None
        if isinstance(response.json, dict):
            net_amount = response.json.get("net_amount")

        if type(net_amount) is not int or net_amount < 1:
            raise InvalidCalculationResponse(employee.employee_key, response.json)

        return net_amount

    def _failure_reason(self, account: Account) -> str:
        if account is None:
            return "O funcionário não tem conta."

        return f"A conta do funcionário está {account.status.enumerator}."

    def _move_money(self, transfer: Transfer, source: Account, destination: Account, bank: Account) -> None:
        fee_amount = transfer.fee_amount

        self.account_repository.add_entry(source, AccountEntry.TRANSFER, AccountEntry.DEBIT, transfer.amount, transfer)

        if fee_amount > 0:
            self.account_repository.add_entry(source, AccountEntry.FEE, AccountEntry.DEBIT, fee_amount, transfer)

        self.account_repository.add_entry(
            destination, AccountEntry.TRANSFER, AccountEntry.CREDIT, transfer.amount, transfer
        )

        if fee_amount > 0:
            self.account_repository.add_entry(bank, AccountEntry.FEE, AccountEntry.CREDIT, fee_amount, transfer)

    def _commit_new_payroll(self, company: Company, reference_month: date, raw_month: str) -> None:
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            if self.payroll_repository.get_not_canceled_by_company_and_month(company, reference_month) is not None:
                raise DuplicatedPayrollMonth(raw_month)

            raise
