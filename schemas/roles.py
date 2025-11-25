from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field, ConfigDict

from .base_model import TunedModel
from .departments import Departments
from .expense_types import ExpenseTypes
from .permissions import GetPermission



class GetRoles(TunedModel):
    id: UUID
    name: str
    is_active: Optional[bool] = None


class GetRole(GetRoles):
    description: Optional[str] = None
    # permissions: Optional[List[GetPermission]] = None
    # departments: Optional[List[Departments]] = None
    # expense_types: Optional[List[ExpenseTypes]] = None
    expense_types: Optional[List[ExpenseTypes]] = Field(alias="expense_types_list")
    departments: Optional[List[Departments]] = Field(alias="departments_list")
    permissions: Optional[List[GetPermission]] = Field(alias="permissions_list")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class CreateRole(TunedModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[List[UUID]] = None
    departments: Optional[List[UUID]] = None
    expense_types: Optional[List[UUID]] = None



class UpdateRole(TunedModel):
    id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[UUID]] = None
    departments: Optional[List[UUID]] = None
    expense_types: Optional[List[UUID]] = None

