from controllers.base_controller import BaseController
from dtos import CompanyDTO
from errors import (
    DuplicatedCompanyDocumentNumber,
    DuplicatedCompanyEmail,
    InvalidCompanyDocumentNumber,
    NotFoundCompany,
)
from repositories import CompanyRepository
from utils.document_number import is_valid_cnpj


class CompanyController(BaseController):

    def __init__(self) -> None:
        super().__init__(__name__)
        self.company_repository = CompanyRepository(self.context)

    def create(self, company_data: dict) -> dict:
        self.logger.debug("Criando uma nova empresa")

        document_number = company_data["document_number"]
        email = company_data["email"]

        if not is_valid_cnpj(document_number):
            raise InvalidCompanyDocumentNumber(document_number)

        if self.company_repository.get_by_document_number(document_number) is not None:
            raise DuplicatedCompanyDocumentNumber(document_number)

        if self.company_repository.get_by_email(email) is not None:
            raise DuplicatedCompanyEmail(email)

        company = self.company_repository.create(company_data=company_data)

        company_dto = CompanyDTO.only_obj_key(company)
        self.session.commit()

        return company_dto

    def get_by_key(self, company_key: str) -> dict:
        self.logger.debug(f"Buscando a empresa de chave {company_key}")

        company = self.company_repository.get_by_key(company_key)

        if company is None:
            raise NotFoundCompany(company_key)

        return CompanyDTO.obj_to_dict(company)

    def update_fee_amount(self, company_key: str, fee_amount: int) -> dict:
        company = self.company_repository.get_by_key(company_key)

        if company is None:
            raise NotFoundCompany(company_key)

        self.company_repository.update_fee_amount(company, fee_amount)

        company_dto = CompanyDTO.only_obj_key(company)
        self.session.commit()

        return company_dto

    def get_list(self, limit: int, offset: int, filters: dict) -> dict:
        companies_list = self.company_repository.list_page(limit, offset, filters)

        # Pedimos um a mais que o limite só pra saber se existe próxima
        # página. Se veio o extra, ele não entra na resposta.
        is_last_page = True
        if len(companies_list) > limit:
            is_last_page = False
            companies_list = companies_list[:-1]

        return {
            "companies_list_dto": CompanyDTO.list_obj_to_list_dict(companies_list),
            "is_last_page": is_last_page,
        }
