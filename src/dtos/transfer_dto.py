from models import Transfer


class TransferDTO:
    @staticmethod
    def obj_to_dict(transfer: Transfer) -> dict:
        destination_account_key = None
        if transfer.destination_account is not None:
            destination_account_key = transfer.destination_account.account_key

        external_destination_dto = None
        if transfer.external_destination is not None:
            external_destination_dto = dict()
            external_destination_dto["bank_code"] = transfer.external_destination.bank_code
            external_destination_dto["branch_number"] = transfer.external_destination.branch_number
            external_destination_dto["account_number"] = transfer.external_destination.account_number

        dto = dict()
        dto["transfer_key"] = transfer.transfer_key
        dto["source_account_key"] = transfer.source_account.account_key
        dto["destination_account_key"] = destination_account_key
        dto["external_destination"] = external_destination_dto
        dto["amount"] = transfer.amount
        dto["fee_amount"] = transfer.fee_amount
        dto["created_at"] = transfer.created_at.isoformat()

        return dto

    @staticmethod
    def receipt(transfer: Transfer) -> dict:
        """O que a criação devolve: a chave e quanto foi cobrado de taxa."""
        dto = dict()
        dto["transfer_key"] = transfer.transfer_key
        dto["fee_amount"] = transfer.fee_amount

        return dto
