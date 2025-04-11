from datetime import datetime
from typing import Optional
from uuid import UUID

from schemas.base_model import TunedModel
from schemas.users import GetUsers
from schemas.clients import Clients


class Log(TunedModel):
    id: UUID
    status: Optional[int]
    user: Optional[GetUsers]
    client: Optional[Clients]
    created_at: Optional[datetime]



class CreateLog(TunedModel):
    status: int
    request_id: UUID
    user_id: UUID
