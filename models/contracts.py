import uuid

from sqlalchemy import Column, ForeignKey, DateTime, func, Boolean, UUID
from sqlalchemy import Integer, String
from sqlalchemy.orm import relationship

from core.base import Base


class Contracts(Base):
    __tablename__ = 'contracts'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID, ForeignKey("requests.id", ondelete="SET NULL"), unique=True)
    request = relationship('Requests', back_populates='contract', lazy='select')
    file = relationship('Files', back_populates='contract', passive_deletes=True, lazy='selectin')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

