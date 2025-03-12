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
    user_id = Column(UUID, ForeignKey("users.id", ondelete="SET NULL"), unique=True)
    head = relationship('Users', back_populates='department', lazy='selectin')
    requests = relationship('Requests', back_populates='department', passive_deletes=True, lazy='noload')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

