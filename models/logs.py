import uuid

from sqlalchemy import Column, ForeignKey, DateTime, func, Boolean, UUID
from sqlalchemy import Integer, String
from sqlalchemy.orm import relationship

from core.base import Base


class Logs(Base):
    __tablename__ = 'logs'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    status = Column(Integer)
    approved = Column(Boolean)
    request_id = Column(UUID, ForeignKey("requests.id", ondelete="CASCADE"))
    request = relationship('Requests', back_populates='logs')
    user_id = Column(UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user = relationship('Users', back_populates='logs')
    client_id = Column(UUID, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    client = relationship('Clients', back_populates='logs')  # lazy="selectin"
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

