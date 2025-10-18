from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from schemas.base_model import TunedModel
from schemas.clients import Clients
from schemas.users import GetUser
from schemas.contracts import Contract
from schemas.departments import Departments
from schemas.expense_types import ExpenseTypes
from schemas.invoices import Invoice
from schemas.logs import Log
from schemas.payer_companies import PayerCompanies
from schemas.payment_types import PaymentTypes


class Requests(TunedModel):
    id: UUID
    number: int
    client: Optional[Clients] = None
    user: Optional[GetUser] = None
    department: Optional[Departments] = None
    expense_type: Optional[ExpenseTypes] = None
    payment_type: Optional[PaymentTypes] = None
    sum: float = None
    sap_code: Optional[str] = None
    approved: Optional[bool] = None
    credit: Optional[bool] = None
    purchase_approved: Optional[bool] = None
    checked_by_financier: Optional[bool] = None
    advance_payment: Optional[bool] = None
    created_at: Optional[datetime] = None
    payment_time: Optional[datetime] = None
    status: Optional[int] = None
    buyer: Optional[str] = None
    supplier: Optional[str] = None
    payment_card: Optional[str] = None
    description: Optional[str] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = None
    payer_company: Optional[PayerCompanies] = None
    contract_number: Optional[str] = None


class Request(Requests):
    currency_sum: Optional[float] = None
    comment: Optional[str] = None
    to_accounting: Optional[bool] = None
    to_transfer: Optional[bool] = None
    approve_comment: Optional[str] = None
    contract: Optional[Contract] = None
    invoice: Optional[Invoice] = None
    receipt: Optional[Invoice] = None
    logs: Optional[List[Log]] = None
    updated_at: Optional[datetime] = None
    expense_type_budget: Optional[float] = 0.0
    department_budget: Optional[float] = 0.0
    invoice_sap_code: Optional[str] = None


class CreateRequest(TunedModel):
    department_id: UUID
    expense_type_id: UUID
    buyer: str
    supplier: str
    city_id: Optional[UUID] = None
    trip_days: Optional[int] = None
    client_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    description: Optional[str] = None
    status: Optional[int] = 0
    sum: Optional[float] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = None
    to_accounting: Optional[bool] = False
    payment_type_id: UUID
    payment_time: Optional[date] = None
    payer_company_id: Optional[UUID] = None
    cash: Optional[float] = None
    payment_card: Optional[str] = None
    sap_code: Optional[str] = None
    contract: Optional[bool] = None
    purchase_approved: Optional[bool] = None
    checked_by_financier: Optional[bool] = None
    contract_number: Optional[str] = None
    file_paths: List[str] = None
    receipt_files: List[str] = None



class UpdateRequest(TunedModel):
    id: UUID
    currency: Optional[str] = None
    sum: Optional[float] = None
    approved: Optional[bool] = None
    credit: Optional[bool] = None
    purchase_approved: Optional[bool] = None
    checked_by_financier: Optional[bool] = None
    to_accounting: Optional[bool] = None
    to_transfer: Optional[bool] = None
    approve_comment: Optional[str] = None
    status: Optional[int] = None
    payment_time: Optional[date] = None
    payment_type_id: Optional[UUID] = None
    comment: Optional[str] = None
    delay_reason: Optional[str] = None
    payer_company_id: Optional[UUID] = None
    invoice: Optional[bool] = None
    file_paths: List[str] = None
    client_id: Optional[UUID] = None
    contract: Optional[bool] = None
    payment_card: Optional[str] = None
    buyer: Optional[str] = None
    supplier: Optional[str] = None
    description: Optional[str] = None
    sap_code: Optional[str] = None
    invoice_sap_code: Optional[str] = None
    contract_number: Optional[str] = None
    department_id: Optional[UUID] = None
    expense_type_id: Optional[UUID] = None



class TransactionRequest(TunedModel):
    id: UUID
    number: int
    expense_type: Optional[ExpenseTypes] = None
    sum: float = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = None
    logs: Optional[List[Log]] = None



class GenerateExcel(TunedModel):
    start_date: date
    finish_date: date
    number: Optional[int] = None
    client: Optional[str] = None
    department_id: Optional[UUID] = None
    supplier: Optional[str] = None
    expense_type_id: Optional[UUID] = None
    payment_type_id: Optional[UUID] = None
    payment_sum: Optional[float] = None
    sap_code: Optional[str] = None
    approved: Optional[bool] = None
    credit: Optional[bool] = None
    created_at: Optional[date] = None
    payment_date: Optional[date] = None
    status: Optional[str] = None

