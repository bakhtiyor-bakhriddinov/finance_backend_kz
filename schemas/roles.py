from datetime import datetime
from typing import List, Optional
from uuid import UUID

from .base_model import TunedModel
from .permissions import GetPermission



class GetRoles(TunedModel):
    id: UUID
    name: str
    is_active: Optional[bool] = None


class GetRole(GetRoles):
    description: Optional[str] = None
    permissions: Optional[List[GetPermission]] = None


class CreateRole(TunedModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[List[UUID]] = None



class UpdateRole(TunedModel):
    id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[UUID]] = None

