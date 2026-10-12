from uuid import uuid4

from database import Context
from models import Company, Position


class PositionRepository:
    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, company: Company, position_data: dict) -> Position:
        position = Position()

        position.position_key = str(uuid4())
        position.company_id = company.id
        position.name = position_data["name"]
        position.salary_amount = position_data["salary_amount"]

        self.session.add(position)
        return position

    def get_by_company_and_key(self, company: Company, position_key: str) -> Position:
        return (
            self.session.query(Position)
            .filter(Position.company_id == company.id, Position.position_key == position_key)
            .first()
        )

    def get_by_company_and_name(self, company: Company, name: str) -> Position:
        return (
            self.session.query(Position)
            .filter(Position.company_id == company.id, Position.name == name)
            .first()
        )

    def list_page_by_company(self, company: Company, limit: int, offset: int) -> list:
        query = self.session.query(Position).filter(Position.company_id == company.id)

        query = query.order_by(Position.created_at.desc(), Position.id.desc())

        return query.limit(limit + 1).offset(offset).all()
