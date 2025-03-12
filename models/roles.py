import uuid

from sqlalchemy import Column, func
from sqlalchemy import String, UUID, Boolean, DateTime
from sqlalchemy.orm import relationship

from core.base import Base


class Roles(Base):
    __tablename__ = 'roles'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    is_active = Column(Boolean, default=True)
    accesses = relationship("Accesses", back_populates="role", cascade="all, delete", lazy='select')
    users = relationship('Users', back_populates='role', passive_deletes=True, lazy='select')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

