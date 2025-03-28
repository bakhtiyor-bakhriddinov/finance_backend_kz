from datetime import datetime
from typing import Optional
from uuid import UUID

from schemas.base_model import TunedModel


class Transactions(TunedModel):
    id: Optional[UUID] = None
    request_id: Optional[UUID] = None
    budget_id: Optional[UUID] = None
    status: Optional[int] = None
    value: Optional[float] = None
    is_income: Optional[bool] = None
    comment: Optional[str] = None
    created_at: Optional[datetime] = None



class Transaction(Transactions):
    updated_at: Optional[datetime] = None



class CreateTransaction(TunedModel):
    request_id: Optional[UUID] = None
    budget_id: Optional[UUID] = None
    value: float
    status: Optional[int] = 5
    comment: Optional[str] = None

