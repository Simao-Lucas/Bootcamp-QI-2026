from uuid import uuid4

from database import Context
from models import Account, ExternalDestination, Payroll, PayrollItem, Transfer


class TransferRepository:
    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(
        self,
        source_account: Account,
        destination_account: Account,
        amount: int,
        fee_amount: int,
        idempotency_key: str,
        payroll: Payroll = None,
        payroll_item: PayrollItem = None,
    ) -> Transfer:
        transfer = Transfer()

        transfer.transfer_key = str(uuid4())
        transfer.source_account = source_account
        transfer.destination_account = destination_account
        transfer.amount = amount
        transfer.fee_amount = fee_amount
        transfer.idempotency_key = idempotency_key
        transfer.payroll = payroll
        transfer.payroll_item = payroll_item

        self.session.add(transfer)
        return transfer

    def add_external_destination(self, transfer: Transfer, destination_data: dict) -> ExternalDestination:
        external_destination = ExternalDestination()

        external_destination.bank_code = destination_data["bank_code"]
        external_destination.branch_number = destination_data["branch_number"]
        external_destination.account_number = destination_data["account_number"]

        transfer.external_destination = external_destination
        return external_destination

    def get_by_key(self, transfer_key: str) -> Transfer:
        return self.session.query(Transfer).filter(Transfer.transfer_key == transfer_key).first()

    def get_by_idempotency_key(self, idempotency_key: str) -> Transfer:
        return self.session.query(Transfer).filter(Transfer.idempotency_key == idempotency_key).first()
