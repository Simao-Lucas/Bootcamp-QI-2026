from typing import List

from models import Company


class CompanyDTO:
    @staticmethod
    def obj_to_dict(company: Company) -> dict:
        dto = dict()
        dto["company_key"] = company.company_key
        dto["name"] = company.name
        dto["document_number"] = company.document_number
        dto["email"] = company.email
        dto["payment_day"] = company.payment_day
        dto["fee_amount"] = company.fee_amount

        return dto

    @staticmethod
    def list_obj_to_list_dict(companies_list: List[Company]) -> List[dict]:
        companies_dict_list = []

        for company in companies_list:
            companies_dict_list.append(CompanyDTO.obj_to_dict(company))

        return companies_dict_list

    @staticmethod
    def only_obj_key(company: Company) -> dict:
        dto = dict()
        dto["company_key"] = company.company_key

        return dto
