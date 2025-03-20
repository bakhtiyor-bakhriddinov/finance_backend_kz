from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from schemas.base_model import TunedModel
from schemas.buyers import Buyers
from schemas.clients import Clients
from schemas.contracts import Contract
from schemas.departments import Departments
from schemas.expense_types import ExpenseTypes
from schemas.invoices import Invoice
from schemas.logs import Log
from schemas.payment_types import PaymentTypes
from schemas.suppliers import Suppliers


class Requests(TunedModel):
    id: UUID
    number: int
    client: Optional[Clients] = None
    department: Optional[Departments] = None
    expense_type: Optional[ExpenseTypes] = None
    payment_type: Optional[PaymentTypes] = None
    sum: float = None
    sap_code: Optional[str] = None
    approved: Optional[bool] = None
    created_at: Optional[datetime] = None
    payment_time: Optional[datetime] = None
    status: Optional[int] = None
    # buyer: Optional[Buyers] = None
    # supplier: Optional[Suppliers] = None
    buyer: Optional[str] = None
    supplier: Optional[str] = None
    payment_card: Optional[str] = None
    description: Optional[str] = None


class Request(Requests):
    comment: Optional[str] = None
    currency: Optional[str] = None
    to_accounting: Optional[bool] = None
    approve_comment: Optional[str] = None
    payer_company: Optional[str] = None
    payment_time: Optional[date] = None
    contract: Optional[Contract] = None
    invoice: Optional[Invoice] = None
    logs: Optional[List[Log]] = None
    updated_at: Optional[datetime] = None


class CreateRequest(TunedModel):
    department_id: UUID
    expense_type_id: UUID
    # buyer_id: UUID
    # supplier_id: UUID
    buyer: str
    supplier: str
    client_id: UUID
    description: Optional[str] = None
    status: Optional[int] = 0
    sum: float
    currency: Optional[str] = None
    to_accounting: Optional[bool] = False
    payment_type_id: UUID
    cash: Optional[float] = None
    payment_card: Optional[str] = None
    sap_code: str
    contract: Optional[bool] = None
    file_paths: List[str] = None



class UpdateRequest(TunedModel):
    id: UUID
    approved: Optional[bool] = None
    to_accounting: Optional[bool] = None
    approve_comment: Optional[str] = None
    status: Optional[int] = None
    payment_time: Optional[date] = None
    payment_type_id: Optional[UUID] = None
    comment: Optional[str] = None
    payer_company: Optional[str] = None
    invoice: Optional[bool] = None
    file_paths: List[str] = None
