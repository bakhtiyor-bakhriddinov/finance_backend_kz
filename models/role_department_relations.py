import uuid

from sqlalchemy import Column, func, ForeignKey
from sqlalchemy import UUID, DateTime
from sqlalchemy.orm import relationship

from core.base import Base


class RoleDepartments(Base):
    __tablename__ = 'role_departments'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID, ForeignKey("roles.id"))
    role = relationship('Roles', back_populates='roles_departments')
    department_id = Column(UUID, ForeignKey("departments.id"))
    department = relationship('Departments', back_populates='roles_departments')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

