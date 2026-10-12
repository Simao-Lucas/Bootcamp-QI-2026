from sqlalchemy import BigInteger, CHAR, Column, Date, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Account, Company, PayrollStatus


class Payroll(Base):
    __tablename__ = "payroll"

    id = Column(Integer, primary_key=True)
    payroll_key = Column(CHAR(36), nullable=False)
    company_id = Column(Integer, ForeignKey(Company.id), nullable=False)
    reference_month = Column(Date, nullable=False)
    total_amount = Column(BigInteger, nullable=False)
    total_fee_amount = Column(BigInteger, nullable=False)
    settlement_account_id = Column(Integer, ForeignKey(Account.id), nullable=True)
    status_id = Column(Integer, ForeignKey(PayrollStatus.id), nullable=False)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("payroll_key"),
        UniqueConstraint("settlement_account_id"),
    )

    company = relationship("Company", foreign_keys=[company_id], lazy="selectin")
    settlement_account = relationship("Account", foreign_keys=[settlement_account_id], lazy="selectin")
    status = relationship("PayrollStatus", foreign_keys=[status_id], lazy="selectin")

    status_events = relationship(
        "PayrollStatusEvent",
        back_populates="payroll",
        order_by="asc(PayrollStatusEvent.event_datetime)",
    )

    items = relationship(
        "PayrollItem",
        back_populates="payroll",
        order_by="asc(PayrollItem.id)",
    )
