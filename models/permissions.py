import uuid

from sqlalchemy import Column, ForeignKey, DateTime, func, Boolean
from sqlalchemy import Integer, String, UUID
from sqlalchemy.orm import relationship
from core.base import Base


class Permissions(Base):
    __tablename__ = 'permissions'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    action = Column(String, unique=True)
    group_id = Column(UUID, ForeignKey('permission_groups.id', ondelete="CASCADE"), nullable=False)
    group = relationship("PermissionGroups", back_populates='permissions')  # lazy="joined"
    is_active = Column(Boolean, default=True)
    accesses = relationship("Accesses", back_populates="permission", cascade="all, delete")  # lazy="joined"
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
