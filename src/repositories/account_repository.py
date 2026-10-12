from datetime import datetime, timedelta
from uuid import uuid4

from database import Context
from models import (
    Account,
    AccountEntry,
    AccountStatus,
    AccountStatusEvent,
    AccountType,
    Company,
    Employee,
    Transfer,
)


class AccountRepository:
    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, type_enumerator: str, company: Company = None, employee: Employee = None) -> Account:
        """A conta nasce com saldo zero, e a abertura já vira o primeiro evento."""
        account = Account()

        account.account_key = str(uuid4())
        account.type = self.get_type(type_enumerator)
        account.company = company
        account.employee = employee
        account.balance_amount = 0

        self.session.add(account)
        self.update_status(account, AccountStatus.ACTIVE)

        return account

    def update_status(self, account: Account, new_status_enumerator: str) -> None:
        new_status = self.get_status(new_status_enumerator)
        account.status = new_status

        new_status_event = AccountStatusEvent()
        new_status_event.status = new_status
        new_status_event.event_datetime = datetime.now()

        account.status_events.append(new_status_event)

    def add_entry(
        self, account: Account, origin: str, entry_type: str, amount: int, transfer: Transfer = None
    ) -> AccountEntry:
        if entry_type == AccountEntry.CREDIT:
            account.balance_amount = account.balance_amount + amount
        else:
            account.balance_amount = account.balance_amount - amount

        entry = AccountEntry()
        entry.account_id = account.id
        entry.origin = origin
        entry.entry_type = entry_type
        entry.amount = amount
        entry.balance_after = account.balance_amount
        entry.transfer = transfer

        self.session.add(entry)
        return entry

    def get_by_key(self, account_key: str) -> Account:
        return self.session.query(Account).filter(Account.account_key == account_key).first()

    def get_by_key_for_update(self, account_key: str) -> Account:
        return (
            self.session.query(Account)
            .filter(Account.account_key == account_key)
            .with_for_update(of=Account)
            .first()
        )

    def lock_by_ids(self, account_ids: list) -> list:
        return (
            self.session.query(Account)
            .filter(Account.id.in_(account_ids))
            .order_by(Account.id)
            .with_for_update(of=Account)
            .populate_existing()
            .all()
        )

    def get_bank_account(self) -> Account:
        return (
            self.session.query(Account)
            .join(AccountType, AccountType.id == Account.type_id)
            .filter(AccountType.enumerator == AccountType.BANK)
            .one()
        )

    def get_by_company(self, company: Company) -> Account:
        return self.session.query(Account).filter(Account.company_id == company.id).first()

    def get_by_employee(self, employee: Employee) -> Account:
        return self.session.query(Account).filter(Account.employee_id == employee.id).first()

    def list_by_employee_ids(self, employee_ids: list) -> list:
        return self.session.query(Account).filter(Account.employee_id.in_(employee_ids)).all()

    def get_type(self, enumerator: str) -> AccountType:
        return self.session.query(AccountType).filter(AccountType.enumerator == enumerator).one()

    def get_status(self, enumerator: str) -> AccountStatus:
        return self.session.query(AccountStatus).filter(AccountStatus.enumerator == enumerator).one()

    def list_entries_page(self, account: Account, limit: int, offset: int, filters: dict) -> list:
        query = self.session.query(AccountEntry).filter(AccountEntry.account_id == account.id)

        date_from = filters.get("date_from")
        if date_from is not None:
            query = query.filter(AccountEntry.created_at >= date_from)

        date_to = filters.get("date_to")
        if date_to is not None:
            query = query.filter(AccountEntry.created_at < date_to + timedelta(days=1))

        query = query.order_by(AccountEntry.created_at.desc(), AccountEntry.id.desc())

        return query.limit(limit + 1).offset(offset).all()
