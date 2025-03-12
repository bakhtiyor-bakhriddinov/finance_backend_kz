import uuid

from sqlalchemy import ForeignKey, Column, Boolean, DateTime, func, BIGINT
from sqlalchemy import Integer, UUID, String
from sqlalchemy.orm import relationship

from core.base import Base


class Clients(Base):
    __tablename__ = 'clients'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    tg_id = Column(BIGINT, index=True, unique=True)
    fullname = Column(String)
    language = Column(String)
    phone = Column(String)
    is_active = Column(Boolean, default=True)
    requests = relationship('Requests', back_populates='client', passive_deletes=True, lazy='select')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

