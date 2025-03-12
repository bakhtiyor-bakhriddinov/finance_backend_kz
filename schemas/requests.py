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


class Request(Requests):
    buyer: Optional[Buyers] = None
    supplier: Optional[Suppliers] = None
    payment_card: Optional[str] = None
    comment: Optional[str] = None
    payer_company: Optional[str] = None
    payment_time: Optional[date] = None
    contract: Optional[Contract] = None
    invoice: Optional[Invoice] = None
    logs: Optional[List[Log]] = None
    updated_at: Optional[datetime] = None


class CreateRequest(TunedModel):
    department_id: UUID
    expense_type_id: UUID
    buyer_id: UUID
    supplier_id: UUID
    client_id: UUID
    description: Optional[str] = None
    status: Optional[int] = 0
    sum: float
    payment_type_id: UUID
    cash: Optional[float] = None
    payment_card: Optional[str] = None
    sap_code: str
    contract: Optional[bool] = None
    file_paths: List[str] = None



class UpdateRequest(TunedModel):
    id: UUID
    approved: Optional[bool] = None
    status: Optional[int] = None
    payment_time: Optional[date] = None
    comment: Optional[str] = None
    payer_company: Optional[str] = None
    invoice: Optional[bool] = None
    file_paths: List[str] = None
