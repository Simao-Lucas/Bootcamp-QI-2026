from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import func

from database import Context
from models import (
    Account,
    Company,
    Employee,
    Payroll,
    PayrollItem,
    PayrollItemStatus,
    PayrollStatus,
    PayrollStatusEvent,
)


class PayrollRepository:
    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, company: Company, reference_month: date) -> Payroll:
        payroll = Payroll()

        payroll.payroll_key = str(uuid4())
        payroll.company = company
        payroll.reference_month = reference_month
        payroll.total_amount = 0
        payroll.total_fee_amount = 0

        self.session.add(payroll)
        self.update_status(payroll, PayrollStatus.PENDING)

        return payroll

    def add_item(
        self, payroll: Payroll, employee: Employee, gross_amount: int, net_amount: int, fee_amount: int
    ) -> PayrollItem:
        item = PayrollItem()

        item.employee = employee
        item.gross_amount = gross_amount
        item.net_amount = net_amount
        item.fee_amount = fee_amount
        item.status = self.get_item_status(PayrollItemStatus.PENDING)
        item.updated_at = datetime.now()

        payroll.items.append(item)
        payroll.total_amount = payroll.total_amount + net_amount
        payroll.total_fee_amount = payroll.total_fee_amount + fee_amount

        return item

    def update_status(self, payroll: Payroll, new_status_enumerator: str) -> None:
        new_status = self.get_status(new_status_enumerator)
        payroll.status = new_status

        new_status_event = PayrollStatusEvent()
        new_status_event.status = new_status
        new_status_event.event_datetime = datetime.now()

        payroll.status_events.append(new_status_event)

    def update_item_status(self, item: PayrollItem, new_status_enumerator: str, failure_reason: str = None) -> None:
        item.status = self.get_item_status(new_status_enumerator)
        item.failure_reason = failure_reason
        item.updated_at = datetime.now()

    def set_settlement_account(self, payroll: Payroll, settlement_account: Account) -> None:
        payroll.settlement_account = settlement_account

    def finish(self, payroll: Payroll) -> None:
        payroll.paid_at = datetime.now()
        self.update_status(payroll, PayrollStatus.PAID)

    def get_by_key(self, payroll_key: str) -> Payroll:
        return self.session.query(Payroll).filter(Payroll.payroll_key == payroll_key).first()

    def get_by_key_for_update(self, payroll_key: str) -> Payroll:
        return (
            self.session.query(Payroll)
            .filter(Payroll.payroll_key == payroll_key)
            .with_for_update(of=Payroll)
            .populate_existing()
            .first()
        )

    def lock_next_to_pay(self) -> Payroll:
        has_pending_item = (
            self.session.query(PayrollItem.id)
            .join(PayrollItemStatus, PayrollItemStatus.id == PayrollItem.status_id)
            .filter(PayrollItem.payroll_id == Payroll.id, PayrollItemStatus.enumerator == PayrollItemStatus.PENDING)
            .exists()
        )

        return (
            self.session.query(Payroll)
            .join(PayrollStatus, PayrollStatus.id == Payroll.status_id)
            .filter(PayrollStatus.enumerator == PayrollStatus.PROCESSING, has_pending_item)
            .order_by(Payroll.id)
            .with_for_update(of=Payroll, skip_locked=True)
            .populate_existing()
            .first()
        )

    def get_not_canceled_by_company_and_month(self, company: Company, reference_month: date) -> Payroll:
        return (
            self.session.query(Payroll)
            .join(PayrollStatus, PayrollStatus.id == Payroll.status_id)
            .filter(
                Payroll.company_id == company.id,
                Payroll.reference_month == reference_month,
                PayrollStatus.enumerator != PayrollStatus.CANCELED,
            )
            .first()
        )

    def list_page_by_company(self, company: Company, limit: int, offset: int, filters: dict) -> list:
        query = self.session.query(Payroll).filter(Payroll.company_id == company.id)

        status = filters.get("status")
        if status is not None:
            query = query.join(PayrollStatus, PayrollStatus.id == Payroll.status_id)
            query = query.filter(PayrollStatus.enumerator == status)

        query = query.order_by(Payroll.created_at.desc(), Payroll.id.desc())

        return query.limit(limit + 1).offset(offset).all()

    def lock_items_by_status(self, payroll: Payroll, status_enumerator: str, limit: int = None) -> list:
        query = (
            self.session.query(PayrollItem)
            .join(PayrollItemStatus, PayrollItemStatus.id == PayrollItem.status_id)
            .filter(PayrollItem.payroll_id == payroll.id, PayrollItemStatus.enumerator == status_enumerator)
            .order_by(PayrollItem.id)
            .with_for_update(of=PayrollItem, skip_locked=True)
            .populate_existing()
        )

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def count_items_by_status(self, payroll: Payroll) -> dict:
        rows = (
            self.session.query(PayrollItemStatus.enumerator, func.count(PayrollItem.id))
            .join(PayrollItem, PayrollItem.status_id == PayrollItemStatus.id)
            .filter(PayrollItem.payroll_id == payroll.id)
            .group_by(PayrollItemStatus.enumerator)
            .all()
        )

        return dict(rows)

    def get_status(self, enumerator: str) -> PayrollStatus:
        return self.session.query(PayrollStatus).filter(PayrollStatus.enumerator == enumerator).one()

    def get_item_status(self, enumerator: str) -> PayrollItemStatus:
        return self.session.query(PayrollItemStatus).filter(PayrollItemStatus.enumerator == enumerator).one()
