from sqlalchemy import Column, ForeignKey, Integer, DateTime, func
from models.base import Base
from sqlalchemy.orm import relationship
from models import Payroll, PayrollStatus


class PayrollStatusEvent(Base):
    __tablename__ = "payroll_status_event"

    id = Column(Integer, primary_key=True)
    payroll_id = Column(Integer, ForeignKey(Payroll.id), nullable=False)
    status_id = Column(Integer, ForeignKey(PayrollStatus.id), nullable=False)
    event_datetime = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    payroll = relationship(
        "Payroll",
        foreign_keys=[payroll_id],
        back_populates="status_events",
        lazy="selectin",
    )
    status = relationship("PayrollStatus", foreign_keys=[status_id], lazy="selectin")
