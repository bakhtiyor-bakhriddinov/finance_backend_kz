from datetime import datetime
from typing import Optional, List
from uuid import UUID

from schemas.base_model import TunedModel



class GetFile(TunedModel):
    id: Optional[UUID] = None
    file_paths: Optional[List[str]] = None
    created_at: Optional[datetime] = None


class CreateFile(TunedModel):
    request_id: UUID
    contract: Optional[bool] = None
    invoice: Optional[bool] = None
    # file_path: str
    # contract_id: Optional[UUID] = None
    # invoice_id: Optional[UUID] = None


