import uuid

from sqlalchemy import Column, ForeignKey, DateTime, func, Boolean, UUID
from sqlalchemy import Integer, String
from sqlalchemy.orm import relationship

from core.base import Base


class ExpenseTypes(Base):
    __tablename__ = 'expense_types'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    is_active = Column(Boolean, default=True)
    requests = relationship('Requests', back_populates='expense_type', passive_deletes=True)  # lazy="joined"
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

