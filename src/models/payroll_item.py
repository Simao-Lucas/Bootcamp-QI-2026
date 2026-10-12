from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Employee, Payroll, PayrollItemStatus


class PayrollItem(Base):
    __tablename__ = "payroll_item"

    id = Column(Integer, primary_key=True)
    payroll_id = Column(Integer, ForeignKey(Payroll.id), nullable=False)
    employee_id = Column(Integer, ForeignKey(Employee.id), nullable=False)
    gross_amount = Column(BigInteger, nullable=False)
    net_amount = Column(BigInteger, nullable=False)
    fee_amount = Column(BigInteger, nullable=False)
    status_id = Column(Integer, ForeignKey(PayrollItemStatus.id), nullable=False)
    failure_reason = Column(String(255), nullable=True)
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("payroll_id", "employee_id"),)

    payroll = relationship(
        "Payroll",
        foreign_keys=[payroll_id],
        back_populates="items",
        lazy="selectin",
    )
    employee = relationship("Employee", foreign_keys=[employee_id], lazy="selectin")
    status = relationship("PayrollItemStatus", foreign_keys=[status_id], lazy="selectin")
