from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Account, Transfer


class AccountEntry(Base):
    __tablename__ = "account_entry"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    transfer_id = Column(Integer, ForeignKey(Transfer.id), nullable=True)
    origin = Column(String(20), nullable=False)
    entry_type = Column(String(10), nullable=False)
    amount = Column(BigInteger, nullable=False)
    balance_after = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    transfer = relationship("Transfer", foreign_keys=[transfer_id], lazy="selectin")

    TRANSFER = "transfer"
    FEE = "fee"
    TEST_CREDIT = "test_credit"

    CREDIT = "credit"
    DEBIT = "debit"
