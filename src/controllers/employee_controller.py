from datetime import date

from controllers.base_controller import BaseController
from dtos import EmployeeDTO
from errors import (
    DuplicatedEmployeeDocumentNumber,
    EmployeeAlreadyTerminated,
    InvalidDate,
    InvalidDocumentNumber,
    NotFoundCompany,
    NotFoundEmployee,
    NotFoundPosition,
    TerminationBeforeHiring,
)
from models import Company, Employee, Position
from repositories import CompanyRepository, EmployeeRepository, PositionRepository
from utils.document_number import is_valid_cpf


class EmployeeController(BaseController):

    def __init__(self) -> None:
        super().__init__(__name__)
        self.company_repository = CompanyRepository(self.context)
        self.position_repository = PositionRepository(self.context)
        self.employee_repository = EmployeeRepository(self.context)

    def create(self, company_key: str, employee_data: dict) -> dict:
        self.logger.debug(f"Criando um novo funcionário na empresa {company_key}")

        company = self._get_company(company_key)
        position = self._get_position(company, employee_data["position_key"])

        document_number = employee_data["document_number"]

        if not is_valid_cpf(document_number):
            raise InvalidDocumentNumber(document_number)

        hired_at = self._parse_date(employee_data["hired_at"])

        if self.employee_repository.get_by_company_and_document_number(company, document_number) is not None:
            raise DuplicatedEmployeeDocumentNumber(document_number)

        employee = self.employee_repository.create(
            company=company, position=position, employee_data=employee_data, hired_at=hired_at
        )

        employee_dto = EmployeeDTO.only_obj_key(employee)
        self.session.commit()

        return employee_dto

    def get_by_key(self, employee_key: str) -> dict:
        self.logger.debug(f"Buscando o funcionário de chave {employee_key}")

        employee = self._get_employee(employee_key)

        return EmployeeDTO.obj_to_dict(employee)

    def get_list(self, company_key: str, limit: int, offset: int, filters: dict) -> dict:
        company = self._get_company(company_key)

        employees_list = self.employee_repository.list_page_by_company(company, limit, offset, filters)

        # Pedimos um a mais que o limite só pra saber se existe próxima
        # página. Se veio o extra, ele não entra na resposta.
        is_last_page = True
        if len(employees_list) > limit:
            is_last_page = False
            employees_list = employees_list[:-1]

        return {
            "employees_list_dto": EmployeeDTO.list_obj_to_list_dict(employees_list),
            "is_last_page": is_last_page,
        }

    def update(self, employee_key: str, update_data: dict) -> dict:
        employee = self._get_employee(employee_key)

        if employee.terminated_at is not None:
            raise EmployeeAlreadyTerminated(employee_key, employee.terminated_at)

        new_position = None
        if "position_key" in update_data:
            new_position = self._get_position(employee.company, update_data["position_key"])

        terminated_at = None
        if "terminated_at" in update_data:
            terminated_at = self._parse_date(update_data["terminated_at"])

            if terminated_at < employee.hired_at:
                raise TerminationBeforeHiring(terminated_at, employee.hired_at)

        if new_position is not None:
            self.employee_repository.update_position(employee, new_position)

        if terminated_at is not None:
            self.employee_repository.terminate(employee, terminated_at)

        employee_dto = EmployeeDTO.only_obj_key(employee)
        self.session.commit()

        return employee_dto

    def _get_company(self, company_key: str) -> Company:
        company = self.company_repository.get_by_key(company_key)

        if company is None:
            raise NotFoundCompany(company_key)

        return company

    def _get_position(self, company: Company, position_key: str) -> Position:
        position = self.position_repository.get_by_company_and_key(company, position_key)

        if position is None:
            raise NotFoundPosition(position_key)

        return position

    def _get_employee(self, employee_key: str) -> Employee:
        employee = self.employee_repository.get_by_key(employee_key)

        if employee is None:
            raise NotFoundEmployee(employee_key)

        return employee

    def _parse_date(self, raw_date: str) -> date:
        try:
            return date.fromisoformat(raw_date)
        except ValueError:
            raise InvalidDate(raw_date)
