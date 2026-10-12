from controllers.base_controller import BaseController
from dtos import PositionDTO
from errors import DuplicatedPositionName, NotFoundCompany
from models import Company
from repositories import CompanyRepository, PositionRepository


class PositionController(BaseController):
    def __init__(self) -> None:
        super().__init__(__name__)
        self.company_repository = CompanyRepository(self.context)
        self.position_repository = PositionRepository(self.context)

    def create(self, company_key: str, position_data: dict) -> dict:
        self.logger.debug(f"Criando um novo cargo na empresa {company_key}")

        company = self._get_company(company_key)
        name = position_data["name"]

        if self.position_repository.get_by_company_and_name(company, name) is not None:
            raise DuplicatedPositionName(name)

        position = self.position_repository.create(company=company, position_data=position_data)

        position_dto = PositionDTO.only_obj_key(position)
        self.session.commit()

        return position_dto

    def get_list(self, company_key: str, limit: int, offset: int) -> dict:
        company = self._get_company(company_key)

        positions_list = self.position_repository.list_page_by_company(company, limit, offset)

        # Pedimos um a mais que o limite só pra saber se existe próxima
        # página. Se veio o extra, ele não entra na resposta.
        is_last_page = True
        if len(positions_list) > limit:
            is_last_page = False
            positions_list = positions_list[:-1]

        return {
            "positions_list_dto": PositionDTO.list_obj_to_list_dict(positions_list),
            "is_last_page": is_last_page,
        }

    def _get_company(self, company_key: str) -> Company:
        company = self.company_repository.get_by_key(company_key)

        if company is None:
            raise NotFoundCompany(company_key)

        return company
