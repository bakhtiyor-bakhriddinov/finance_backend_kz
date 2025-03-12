import uuid

from sqlalchemy import Column, ForeignKey, DateTime, func, Boolean, UUID, DECIMAL, Text, Integer, BIGINT, String
from sqlalchemy.orm import relationship

from core.base import Base
from core.session import serial_seq


class Requests(Base):
    __tablename__ = 'requests'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    number = Column(BIGINT, serial_seq, server_default=serial_seq.next_value(), unique=True, nullable=False)
    sum = Column(DECIMAL, nullable=False)
    sap_code = Column(String)
    approved = Column(Boolean, default=False)
    payment_time = Column(DateTime(timezone=True))
    payment_card = Column(String)
    cash = Column(DECIMAL)
    description = Column(Text)
    comment = Column(Text)
    payer_company = Column(String)
    status = Column(Integer)
    contract = relationship('Contracts', back_populates='request', uselist=False, passive_deletes=True, lazy='selectin')
    invoice = relationship('Invoices', back_populates='request', uselist=False, passive_deletes=True, lazy='selectin')
    client_id = Column(UUID, ForeignKey("clients.id", ondelete="SET NULL"))
    client = relationship('Clients', back_populates='requests', lazy='selectin')
    department_id = Column(UUID, ForeignKey("departments.id", ondelete="SET NULL"))
    department = relationship('Departments', back_populates='requests', lazy='selectin')
    expense_type_id = Column(UUID, ForeignKey("expense_types.id", ondelete="SET NULL"))
    expense_type = relationship('ExpenseTypes', back_populates='requests', lazy='selectin')
    payment_type_id = Column(UUID, ForeignKey("payment_types.id", ondelete="SET NULL"))
    payment_type = relationship('PaymentTypes', back_populates='requests', lazy='selectin')
    buyer_id = Column(UUID, ForeignKey("buyers.id", ondelete="SET NULL"))
    buyer = relationship('Buyers', back_populates='requests', lazy='selectin')
    supplier_id = Column(UUID, ForeignKey("suppliers.id", ondelete="SET NULL"))
    supplier = relationship('Suppliers', back_populates='requests', lazy='selectin')
    logs = relationship('Logs', back_populates='request', cascade="all, delete", lazy='selectin')
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

