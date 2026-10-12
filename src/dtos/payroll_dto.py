from typing import List

from models import Payroll, PayrollItem


class PayrollDTO:
    @staticmethod
    def obj_to_dict(payroll: Payroll) -> dict:
        settlement_account_key = None
        settlement_balance_amount = None
        if payroll.settlement_account is not None:
            settlement_account_key = payroll.settlement_account.account_key
            settlement_balance_amount = payroll.settlement_account.balance_amount

        dto = PayrollDTO.summary(payroll)
        dto["company_key"] = payroll.company.company_key
        dto["settlement_account_key"] = settlement_account_key
        dto["settlement_balance_amount"] = settlement_balance_amount
        dto["status_events"] = []
        dto["items"] = []

        for status_event in payroll.status_events:
            status_event_dto = dict()
            status_event_dto["status"] = status_event.status.enumerator
            status_event_dto["event_datetime"] = status_event.event_datetime.isoformat()

            dto["status_events"].append(status_event_dto)

        for item in payroll.items:
            dto["items"].append(PayrollDTO.item_to_dict(item))

        return dto

    @staticmethod
    def summary(payroll: Payroll) -> dict:
        paid_at = None
        if payroll.paid_at is not None:
            paid_at = payroll.paid_at.isoformat()

        dto = dict()
        dto["payroll_key"] = payroll.payroll_key
        dto["reference_month"] = payroll.reference_month.strftime("%Y-%m")
        dto["status"] = payroll.status.enumerator
        dto["total_amount"] = payroll.total_amount
        dto["total_fee_amount"] = payroll.total_fee_amount
        dto["paid_at"] = paid_at
        dto["created_at"] = payroll.created_at.isoformat()

        return dto

    @staticmethod
    def item_to_dict(item: PayrollItem) -> dict:
        dto = dict()
        dto["employee_key"] = item.employee.employee_key
        dto["gross_amount"] = item.gross_amount
        dto["net_amount"] = item.net_amount
        dto["fee_amount"] = item.fee_amount
        dto["status"] = item.status.enumerator
        dto["failure_reason"] = item.failure_reason

        return dto

    @staticmethod
    def list_obj_to_list_dict(payrolls_list: List[Payroll]) -> List[dict]:
        payrolls_dict_list = []

        for payroll in payrolls_list:
            payrolls_dict_list.append(PayrollDTO.summary(payroll))

        return payrolls_dict_list
