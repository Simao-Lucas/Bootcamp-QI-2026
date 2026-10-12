from sqlalchemy import CHAR, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Transfer


class ExternalDestination(Base):
    __tablename__ = "external_destination"

    id = Column(Integer, primary_key=True)
    transfer_id = Column(Integer, ForeignKey(Transfer.id), nullable=False)
    bank_code = Column(CHAR(3), nullable=False)
    branch_number = Column(CHAR(4), nullable=False)
    account_number = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("transfer_id"),)

    transfer = relationship("Transfer", foreign_keys=[transfer_id], back_populates="external_destination")
