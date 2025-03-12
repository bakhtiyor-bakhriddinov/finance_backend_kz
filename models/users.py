import uuid

from sqlalchemy import Integer, BIGINT, String, DateTime, UUID, Boolean
from sqlalchemy import ForeignKey, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.base import Base



class Users(Base):
    __tablename__ = 'users'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    tg_id = Column(BIGINT, index=True, unique=True)
    fullname = Column(String)
    language = Column(String)
    phone = Column(String)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String)
    is_active = Column(Boolean, default=True)
    role_id = Column(UUID, ForeignKey("roles.id", ondelete="SET NULL"))
    role = relationship('Roles', back_populates='users', lazy='selectin')
    department = relationship('Departments', back_populates='head', uselist=False, passive_deletes=True, lazy='select')
    logs = relationship('Logs', back_populates='user', passive_deletes=True, lazy='select')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

