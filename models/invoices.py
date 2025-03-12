import uuid

from sqlalchemy import Column, ForeignKey, DateTime, func, UUID
from sqlalchemy.orm import relationship

from core.base import Base


class Invoices(Base):
    __tablename__ = 'invoices'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID, ForeignKey("requests.id", ondelete="SET NULL"), unique=True)
    request = relationship('Requests', back_populates='invoice')  # lazy="joined"
    file = relationship('Files', back_populates='invoice', passive_deletes=True)  # lazy="joined"
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

