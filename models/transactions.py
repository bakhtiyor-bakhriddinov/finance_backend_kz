import uuid

from sqlalchemy import Column, func, ForeignKey, DECIMAL, Date, Integer
from sqlalchemy import String, UUID, Boolean, DateTime
from sqlalchemy.orm import relationship

from core.base import Base


class Transactions(Base):
    __tablename__ = 'transactions'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID, ForeignKey("requests.id"))
    request = relationship('Requests', back_populates='transaction')
    budget_id = Column(UUID, ForeignKey("budgets.id"))
    budget = relationship('Budgets', back_populates='transactions')
    status = Column(Integer)
    value = Column(DECIMAL)
    is_income = Column(Boolean)
    comment = Column(String)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

