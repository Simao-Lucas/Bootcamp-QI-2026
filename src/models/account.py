from sqlalchemy import BigInteger, CHAR, Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import AccountStatus, AccountType, Company, Employee


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True)
    account_key = Column(CHAR(36), nullable=False)
    type_id = Column(Integer, ForeignKey(AccountType.id), nullable=False)
    company_id = Column(Integer, ForeignKey(Company.id), nullable=True)
    employee_id = Column(Integer, ForeignKey(Employee.id), nullable=True)
    balance_amount = Column(BigInteger, nullable=False)
    status_id = Column(Integer, ForeignKey(AccountStatus.id), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("account_key"),
        UniqueConstraint("company_id"),
        UniqueConstraint("employee_id"),
    )

    type = relationship("AccountType", foreign_keys=[type_id], lazy="selectin")
    status = relationship("AccountStatus", foreign_keys=[status_id], lazy="selectin")
    company = relationship("Company", foreign_keys=[company_id], lazy="selectin")
    employee = relationship("Employee", foreign_keys=[employee_id], lazy="selectin")

    status_events = relationship(
        "AccountStatusEvent",
        back_populates="account",
        order_by="asc(AccountStatusEvent.event_datetime)",
    )
