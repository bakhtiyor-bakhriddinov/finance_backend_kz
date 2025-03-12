import uuid

from sqlalchemy import Column, ForeignKey, DateTime, func, String, UUID
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from core.base import Base


class Files(Base):
    __tablename__ = 'files'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    file_paths = Column(ARRAY(String), nullable=False)
    contract_id = Column(UUID, ForeignKey("contracts.id", ondelete="SET NULL"))
    contract = relationship('Contracts', back_populates='file', lazy='select')
    invoice_id = Column(UUID, ForeignKey("invoices.id", ondelete="SET NULL"))
    invoice = relationship('Invoices', back_populates='file', lazy='select')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

