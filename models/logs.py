import uuid

from sqlalchemy import Column, ForeignKey, DateTime, func, Boolean, UUID
from sqlalchemy import Integer, String
from sqlalchemy.orm import relationship

from core.base import Base


class Logs(Base):
    __tablename__ = 'logs'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    status = Column(Integer)
    request_id = Column(UUID, ForeignKey("requests.id", ondelete="CASCADE"))
    request = relationship('Requests', back_populates='logs')  # lazy="joined"
    user_id = Column(UUID, ForeignKey("users.id", ondelete="SET NULL"))
    user = relationship('Users', back_populates='logs')  # lazy="joined"
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

