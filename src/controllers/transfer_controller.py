from sqlalchemy.exc import IntegrityError

from controllers.base_controller import BaseController
from dtos import TransferDTO
from errors import (
    AccountNotActive,
    BankAccountAsDestination,
    DuplicatedIdempotencyKey,
    InsufficientBalance,
    NotFoundAccount,
    NotFoundTransfer,
    SameAccountTransfer,
    SettlementAccountTransfer,
)
from models import Account, AccountEntry, AccountStatus, AccountType, Transfer
from repositories import AccountRepository, TransferRepository


class TransferController(BaseController):

    def __init__(self) -> None:
        super().__init__(__name__)
        self.transfer_repository = TransferRepository(self.context)
        self.account_repository = AccountRepository(self.context)

    def create(self, transfer_data: dict) -> dict:
        source_account_key = transfer_data["source_account_key"]
        destination_account_key = transfer_data["destination_account_key"]
        amount = transfer_data["amount"]
        idempotency_key = transfer_data["idempotency_key"]

        self.logger.debug(f"Transferindo {amount} de {source_account_key} para {destination_account_key}")

        source = self._get_account(source_account_key)
        destination = self._get_account(destination_account_key)

        if source.id == destination.id:
            raise SameAccountTransfer(source_account_key)

        if destination.type.enumerator == AccountType.BANK:
            raise BankAccountAsDestination(destination_account_key)

        self._check_not_settlement(source, source_account_key)
        self._check_not_settlement(destination, destination_account_key)

        fee_amount = self._fee_of(source)
        bank = self._lock_accounts([source, destination])

        original = self.transfer_repository.get_by_idempotency_key(idempotency_key)
        if original is not None:
            return self._replay(original, self._is_same_internal_request(original, transfer_data))

        self._check_active(source, source_account_key)
        self._check_active(destination, destination_account_key)
        self._check_balance(source, source_account_key, amount, fee_amount)

        transfer = self.transfer_repository.create(source, destination, amount, fee_amount, idempotency_key)
        self._move_money(transfer, source, destination, bank)

        transfer_dto = TransferDTO.receipt(transfer)
        self._commit(idempotency_key)

        return {"transfer_dto": transfer_dto, "is_new": True}

    def create_external(self, transfer_data: dict) -> dict:
        source_account_key = transfer_data["source_account_key"]
        amount = transfer_data["amount"]
        idempotency_key = transfer_data["idempotency_key"]

        self.logger.debug(f"Transferindo {amount} de {source_account_key} para outro banco")

        source = self._get_account(source_account_key)
        self._check_not_settlement(source, source_account_key)

        fee_amount = self._fee_of(source)
        bank = self._lock_accounts([source])

        original = self.transfer_repository.get_by_idempotency_key(idempotency_key)
        if original is not None:
            return self._replay(original, self._is_same_external_request(original, transfer_data))

        self._check_active(source, source_account_key)
        self._check_balance(source, source_account_key, amount, fee_amount)

        transfer = self.transfer_repository.create(source, None, amount, fee_amount, idempotency_key)
        self.transfer_repository.add_external_destination(transfer, transfer_data["destination"])
        self._move_money(transfer, source, None, bank)

        transfer_dto = TransferDTO.receipt(transfer)
        self._commit(idempotency_key)

        return {"transfer_dto": transfer_dto, "is_new": True}

    def get_by_key(self, transfer_key: str) -> dict:
        self.logger.debug(f"Buscando a transferência de chave {transfer_key}")

        transfer = self.transfer_repository.get_by_key(transfer_key)

        if transfer is None:
            raise NotFoundTransfer(transfer_key)

        return TransferDTO.obj_to_dict(transfer)

    def _get_account(self, account_key: str) -> Account:
        account = self.account_repository.get_by_key(account_key)

        if account is None:
            raise NotFoundAccount(account_key)

        return account

    def _check_not_settlement(self, account: Account, account_key: str) -> None:
        if account.type.enumerator == AccountType.SETTLEMENT:
            raise SettlementAccountTransfer(account_key)

    def _fee_of(self, account: Account) -> int:
        if account.company is not None:
            return account.company.fee_amount

        if account.employee is not None:
            return account.employee.company.fee_amount

        return 0

    def _lock_accounts(self, accounts: list) -> Account:
        bank = self.account_repository.get_bank_account()

        account_ids = {bank.id}
        for account in accounts:
            account_ids.add(account.id)

        self.account_repository.lock_by_ids(sorted(account_ids))

        return bank

    def _replay(self, original: Transfer, is_same_request: bool) -> dict:
        if not is_same_request:
            raise DuplicatedIdempotencyKey(original.idempotency_key)

        return {"transfer_dto": TransferDTO.receipt(original), "is_new": False}

    def _is_same_internal_request(self, transfer: Transfer, transfer_data: dict) -> bool:
        if transfer.destination_account is None:
            return False

        return (
            transfer.source_account.account_key == transfer_data["source_account_key"]
            and transfer.destination_account.account_key == transfer_data["destination_account_key"]
            and transfer.amount == transfer_data["amount"]
        )

    def _is_same_external_request(self, transfer: Transfer, transfer_data: dict) -> bool:
        external_destination = transfer.external_destination
        if external_destination is None:
            return False

        destination_data = transfer_data["destination"]

        return (
            transfer.source_account.account_key == transfer_data["source_account_key"]
            and transfer.amount == transfer_data["amount"]
            and external_destination.bank_code == destination_data["bank_code"]
            and external_destination.branch_number == destination_data["branch_number"]
            and external_destination.account_number == destination_data["account_number"]
        )

    def _check_active(self, account: Account, account_key: str) -> None:
        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

    def _check_balance(self, account: Account, account_key: str, amount: int, fee_amount: int) -> None:
        needed_amount = amount + fee_amount

        if account.balance_amount < needed_amount:
            raise InsufficientBalance(account_key, account.balance_amount, needed_amount)

    def _move_money(self, transfer: Transfer, source: Account, destination: Account, bank: Account) -> None:
        fee_amount = transfer.fee_amount

        self.account_repository.add_entry(source, AccountEntry.TRANSFER, AccountEntry.DEBIT, transfer.amount, transfer)

        if fee_amount > 0:
            self.account_repository.add_entry(source, AccountEntry.FEE, AccountEntry.DEBIT, fee_amount, transfer)

        if destination is not None:
            self.account_repository.add_entry(
                destination, AccountEntry.TRANSFER, AccountEntry.CREDIT, transfer.amount, transfer
            )

        if fee_amount > 0:
            self.account_repository.add_entry(bank, AccountEntry.FEE, AccountEntry.CREDIT, fee_amount, transfer)

    def _commit(self, idempotency_key: str) -> None:
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            if self.transfer_repository.get_by_idempotency_key(idempotency_key) is not None:
                raise DuplicatedIdempotencyKey(idempotency_key)

            raise
