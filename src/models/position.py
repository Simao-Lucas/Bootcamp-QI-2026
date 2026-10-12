from sqlalchemy import BigInteger, CHAR, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from models.base import Base
from models import Company


class Position(Base):
    __tablename__ = "position"

    id = Column(Integer, primary_key=True)
    position_key = Column(CHAR(36), nullable=False)
    company_id = Column(Integer, ForeignKey(Company.id), nullable=False)
    name = Column(String(255), nullable=False)
    salary_amount = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("position_key"),
        UniqueConstraint("company_id", "name"),
    )
