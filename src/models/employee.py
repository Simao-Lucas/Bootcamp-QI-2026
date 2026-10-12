from sqlalchemy import CHAR, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Company, Position


class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True)
    employee_key = Column(CHAR(36), nullable=False)
    company_id = Column(Integer, ForeignKey(Company.id), nullable=False)
    position_id = Column(Integer, ForeignKey(Position.id), nullable=False)
    name = Column(String(255), nullable=False)
    document_number = Column(CHAR(14), nullable=False)
    email = Column(String(255), nullable=False)
    hired_at = Column(Date, nullable=False)
    terminated_at = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("employee_key"),
        UniqueConstraint("company_id", "document_number"),
    )

    company = relationship("Company", foreign_keys=[company_id], lazy="selectin")
    position = relationship("Position", foreign_keys=[position_id], lazy="selectin")
