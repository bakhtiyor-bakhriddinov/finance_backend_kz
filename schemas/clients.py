from datetime import datetime
from typing import Optional
from uuid import UUID

from schemas.base_model import TunedModel


class Clients(TunedModel):
    id: UUID
    fullname: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool]
    tg_id: Optional[int]
    created_at: Optional[datetime]



class Client(Clients):
    language: Optional[str]
    updated_at: Optional[datetime] = None



class UpdateClient(TunedModel):
    id: UUID
    fullname: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None


class CreateClient(TunedModel):
    tg_id: int
    fullname: str
    language: Optional[str] = 'ru'
    phone: str
