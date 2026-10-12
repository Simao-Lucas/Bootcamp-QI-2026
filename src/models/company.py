from sqlalchemy import BigInteger, CHAR, Column, DateTime, Integer, SmallInteger, String, UniqueConstraint, func
from models.base import Base


class Company(Base):
    __tablename__ = "company"

    id = Column(Integer, primary_key=True)
    company_key = Column(CHAR(36), nullable=False)
    name = Column(String(255), nullable=False)
    document_number = Column(CHAR(18), nullable=False)
    email = Column(String(255), nullable=False)
    payment_day = Column(SmallInteger, nullable=False)
    fee_amount = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("company_key"),
        UniqueConstraint("document_number"),
        UniqueConstraint("email"),
    )
