from datetime import datetime, date
from typing import Optional
from uuid import UUID

from schemas.base_model import TunedModel
from schemas.departments import Departments
from schemas.expense_types import ExpenseTypes
from schemas.transactions import Transactions


class Budgets(TunedModel):
    id: UUID
    expense_type: Optional[ExpenseTypes] = None
    department: Optional[Departments] = None
    value: Optional[float] = None
    created_at: Optional[datetime]


class Budget(Budgets):
    transactions: Optional[Transactions] = None
    updated_at: Optional[datetime] = None


class CreateBudget(TunedModel):
    expense_type_id: UUID
    department_id: UUID
    start_date: date
    finish_date: date


