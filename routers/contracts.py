from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.session import get_db
from dal.dao import ContractDAO
from schemas.contracts import Contract, CreateContract
from utils.utils import PermissionChecker

contracts_router = APIRouter()




@contracts_router.post("/contracts", response_model=Contract)
async def create_contract(
        body: CreateContract,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Контракты": ["create"]}))
):
    created_obj = await ContractDAO.add(session=db, **body.model_dump())
    db.commit()
    db.refresh(created_obj)
    return created_obj



# @contracts_router.get("/contracts", response_model=List[Suppliers])
# async def get_contract_list(
#         db: AsyncSession = Depends(get_db),
#         current_user: dict = Depends(PermissionChecker(required_permissions={"Контракты": ["read"]}))
# ):
#     objs = await SupplierDAO.get_all(session=db)
#     return objs



@contracts_router.get("/contracts/{id}", response_model=Contract)
async def get_contract(
        id: UUID,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Контракты": ["read"]}))
):
    obj = await ContractDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    return obj



