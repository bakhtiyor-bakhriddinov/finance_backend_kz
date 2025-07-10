from datetime import datetime
from typing import Optional, List
from uuid import UUID

from schemas.base_model import TunedModel



class ClientUser(TunedModel):
    id: UUID
    username: str
    tg_id: Optional[int] = None
    fullname: Optional[str] = None
    is_active: Optional[bool]
    phone: Optional[str] = None
    created_at: Optional[datetime]


class ClientDepartments(TunedModel):
    id: Optional[UUID] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None
    over_budget: Optional[bool] = None
    balance: Optional[float] = None
    created_at: Optional[datetime]



class Clients(TunedModel):
    id: UUID
    fullname: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool]
    tg_id: Optional[int]
    web_user: Optional[bool] = None
    department: Optional[List[ClientDepartments]] = None
    created_at: Optional[datetime]



class Client(Clients):
    language: Optional[str]
    user: Optional[ClientUser] = None
    updated_at: Optional[datetime] = None



class UpdateClient(TunedModel):
    id: UUID
    user_id: Optional[UUID] = None
    fullname: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None
    web_user: Optional[bool] = None


class CreateClient(TunedModel):
    tg_id: int
    fullname: str
    language: Optional[str] = 'ru'
    phone: str
