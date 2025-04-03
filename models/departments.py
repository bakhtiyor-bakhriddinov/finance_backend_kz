import uuid

from sqlalchemy import Integer, UUID, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Column
from core.base import Base



class Departments(Base):
    __tablename__ = 'departments'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    over_budget = Column(Boolean, default=False)
    client_id = Column(UUID, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True) # unique=True
    head = relationship('Clients', back_populates='department') # lazy="selectin"
    requests = relationship('Requests', back_populates='department', passive_deletes=True) # lazy='select'
    budgets = relationship('Budgets', back_populates='department')
    roles_departments = relationship('RoleDepartments', back_populates='department')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

