import uuid

from sqlalchemy import Column, func, ForeignKey
from sqlalchemy import UUID, DateTime
from sqlalchemy.orm import relationship

from core.base import Base


class RoleExpenseTypes(Base):
    __tablename__ = 'role_expense_types'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID, ForeignKey("roles.id"))
    role = relationship('Roles', back_populates='expense_types')
    expense_type_id = Column(UUID, ForeignKey("expense_types.id"))
    expense_type = relationship('ExpenseTypes', back_populates='roles')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

