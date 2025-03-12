import uuid

from sqlalchemy import (
    Column,
    ForeignKey,
    DateTime,
    Integer,
    UUID
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.base import Base


class Accesses(Base):
    __tablename__ = "accesses"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    permission_id = Column(UUID, ForeignKey('permissions.id', ondelete="CASCADE"), nullable=False)
    permission = relationship('Permissions', back_populates='accesses', lazy='select')
    role_id = Column(UUID, ForeignKey('roles.id', ondelete="CASCADE"), nullable=False)
    role = relationship("Roles", back_populates="accesses", lazy='select')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

