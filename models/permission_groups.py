import uuid

from sqlalchemy import Column, ForeignKey, func
from sqlalchemy import UUID, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from core.base import Base


class PermissionGroups(Base):
    __tablename__ = 'permission_groups'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    permissions = relationship("Permissions", back_populates="group", cascade="all, delete")  # lazy="joined"
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
