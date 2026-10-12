from typing import List

from models import Account, AccountEntry


class AccountDTO:

    @staticmethod
    def obj_to_dict(account: Account) -> dict:
        company_key = None
        if account.company is not None:
            company_key = account.company.company_key

        employee_key = None
        if account.employee is not None:
            employee_key = account.employee.employee_key

        dto = dict()
        dto["account_key"] = account.account_key
        dto["account_type"] = account.type.enumerator
        dto["company_key"] = company_key
        dto["employee_key"] = employee_key
        dto["balance_amount"] = account.balance_amount
        dto["status"] = account.status.enumerator
        dto["status_events"] = []

        for status_event in account.status_events:
            status_event_dto = dict()
            status_event_dto["status"] = status_event.status.enumerator
            status_event_dto["event_datetime"] = status_event.event_datetime.isoformat()

            dto["status_events"].append(status_event_dto)

        return dto

    @staticmethod
    def only_obj_key(account: Account) -> dict:
        dto = dict()
        dto["account_key"] = account.account_key

        return dto

    @staticmethod
    def balance(account: Account) -> dict:
        dto = dict()
        dto["account_key"] = account.account_key
        dto["balance_amount"] = account.balance_amount

        return dto


class AccountEntryDTO:
    @staticmethod
    def obj_to_dict(entry: AccountEntry) -> dict:
        transfer_key = None
        if entry.transfer is not None:
            transfer_key = entry.transfer.transfer_key

        dto = dict()
        dto["origin"] = entry.origin
        dto["entry_type"] = entry.entry_type
        dto["amount"] = entry.amount
        dto["balance_after"] = entry.balance_after
        dto["transfer_key"] = transfer_key
        dto["created_at"] = entry.created_at.isoformat()

        return dto

    @staticmethod
    def list_obj_to_list_dict(entries_list: List[AccountEntry]) -> List[dict]:
        entries_dict_list = []

        for entry in entries_list:
            entries_dict_list.append(AccountEntryDTO.obj_to_dict(entry))

        return entries_dict_list
