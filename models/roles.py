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
    accesses = relationship("Accesses", back_populates="role", cascade="all, delete")
    users = relationship('Users', back_populates='role', passive_deletes=True)
    roles_departments = relationship('RoleDepartments', back_populates='role')
    expense_types = relationship('RoleExpenseTypes', back_populates='role')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @property
    def expense_types_list(self):
        return [rel.expense_type for rel in self.expense_types]

    @property
    def departments(self):
        return [rel.department for rel in self.roles_departments]

    @property
    def permissions(self):
        return [rel.permission for rel in self.accesses]

