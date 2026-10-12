from sqlalchemy import BigInteger, CHAR, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Account, Payroll, PayrollItem


class Transfer(Base):
    __tablename__ = "transfer"

    id = Column(Integer, primary_key=True)
    transfer_key = Column(CHAR(36), nullable=False)
    source_account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    destination_account_id = Column(Integer, ForeignKey(Account.id), nullable=True)
    amount = Column(BigInteger, nullable=False)
    fee_amount = Column(BigInteger, nullable=False)
    payroll_id = Column(Integer, ForeignKey(Payroll.id), nullable=True)
    payroll_item_id = Column(Integer, ForeignKey(PayrollItem.id), nullable=True)
    idempotency_key = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("transfer_key"),
        UniqueConstraint("idempotency_key"),
        UniqueConstraint("payroll_id"),
        UniqueConstraint("payroll_item_id"),
    )

    payroll = relationship("Payroll", foreign_keys=[payroll_id])
    payroll_item = relationship("PayrollItem", foreign_keys=[payroll_item_id])

    source_account = relationship("Account", foreign_keys=[source_account_id], lazy="selectin")
    destination_account = relationship("Account", foreign_keys=[destination_account_id], lazy="selectin")

    external_destination = relationship(
        "ExternalDestination",
        back_populates="transfer",
        uselist=False,
        lazy="selectin",
    )
