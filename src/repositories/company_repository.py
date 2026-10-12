from uuid import uuid4

from database import Context
from models import Company


class CompanyRepository:
    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, company_data: dict) -> Company:
        company = Company()

        company.company_key = str(uuid4())
        company.name = company_data["name"]
        company.document_number = company_data["document_number"]
        company.email = company_data["email"]
        company.payment_day = company_data["payment_day"]
        company.fee_amount = company_data["fee_amount"]

        self.session.add(company)
        return company

    def update_fee_amount(self, company: Company, fee_amount: int) -> None:
        company.fee_amount = fee_amount

    def get_by_key(self, company_key: str) -> Company:
        return self.session.query(Company).filter(Company.company_key == company_key).first()

    def get_by_document_number(self, document_number: str) -> Company:
        return self.session.query(Company).filter(Company.document_number == document_number).first()

    def get_by_email(self, email: str) -> Company:
        return self.session.query(Company).filter(Company.email == email).first()

    def list_page(self, limit: int, offset: int, filters: dict) -> list:
        query = self.session.query(Company)

        name = filters.get("name")
        if name is not None:
            query = query.filter(Company.name.ilike(f"%{name}%"))

        query = query.order_by(Company.created_at.desc(), Company.id.desc())

        return query.limit(limit + 1).offset(offset).all()
