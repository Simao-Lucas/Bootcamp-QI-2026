from datetime import date
from uuid import uuid4

from database import Context
from models import Company, Employee, Position


class EmployeeRepository:
    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, company: Company, position: Position, employee_data: dict, hired_at: date) -> Employee:
        employee = Employee()

        employee.employee_key = str(uuid4())
        employee.company = company
        employee.position = position
        employee.name = employee_data["name"]
        employee.document_number = employee_data["document_number"]
        employee.email = employee_data["email"]
        employee.hired_at = hired_at

        self.session.add(employee)
        return employee

    def update_position(self, employee: Employee, position: Position) -> None:
        employee.position = position

    def terminate(self, employee: Employee, terminated_at: date) -> None:
        employee.terminated_at = terminated_at

    def get_by_key(self, employee_key: str) -> Employee:
        return self.session.query(Employee).filter(Employee.employee_key == employee_key).first()

    def get_by_company_and_document_number(self, company: Company, document_number: str) -> Employee:
        return (
            self.session.query(Employee)
            .filter(Employee.company_id == company.id, Employee.document_number == document_number)
            .first()
        )

    def list_active_by_company(self, company: Company) -> list:
        return (
            self.session.query(Employee)
            .filter(Employee.company_id == company.id, Employee.terminated_at.is_(None))
            .order_by(Employee.id)
            .all()
        )

    def list_page_by_company(self, company: Company, limit: int, offset: int, filters: dict) -> list:
        query = self.session.query(Employee).filter(Employee.company_id == company.id)

        name = filters.get("name")
        if name is not None:
            query = query.filter(Employee.name.ilike(f"%{name}%"))

        active = filters.get("active")
        if active is True:
            query = query.filter(Employee.terminated_at.is_(None))
        elif active is False:
            query = query.filter(Employee.terminated_at.is_not(None))

        query = query.order_by(Employee.created_at.desc(), Employee.id.desc())

        return query.limit(limit + 1).offset(offset).all()
