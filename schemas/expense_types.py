from datetime import datetime
from typing import Optional
from uuid import UUID

from schemas.base_model import TunedModel


class ExpenseTypes(TunedModel):
    id: UUID
    name: str
    is_active: Optional[bool]
    created_at: Optional[datetime]


class ExpenseType(ExpenseTypes):
    description: Optional[str] = None
    updated_at: Optional[datetime] = None


class CreateExpenseType(TunedModel):
    name: str
    description: Optional[str] = None


class UpdateExpenseType(TunedModel):
    id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    purchasable: Optional[bool] = None
