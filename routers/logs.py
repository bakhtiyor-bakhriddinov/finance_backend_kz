from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.session import get_db
from dal.dao import LogDAO
from schemas.suppliers import Suppliers, Supplier, CreateSupplier, UpdateSupplier
from schemas.logs import Log, CreateLog
from utils.utils import PermissionChecker



logs_router = APIRouter()


@logs_router.post("/logs", response_model=Log)
async def create_log(
        body: CreateLog,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Логи": ["create"]}))
):
    created_obj = await LogDAO.add(session=db, **body.model_dump())
    db.commit()
    db.refresh(created_obj)
    return created_obj



# @logs_router.get("/logs", response_model=List[Log])
# async def get_request_logs(
#         request_id: UUID,
#         db: AsyncSession = Depends(get_db),
#         current_user: dict = Depends(PermissionChecker(required_permissions={"Логи": ["read"]}))
# ):
#     objs = await LogDAO.get_all(session=db, filters={"request_id": request_id})
#     return objs



# @logs_router.get("/logs/{id}", response_model=Log)
# async def get_log(
#         id: UUID,
#         db: AsyncSession = Depends(get_db),
#         current_user: dict = Depends(PermissionChecker(required_permissions={"Логи": ["read"]}))
# ):
#     obj = await LogDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
#     return obj



