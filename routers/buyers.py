from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.session import get_db
from dal.dao import BuyerDAO
from schemas.buyers import Buyer, Buyers, CreateBuyer, UpdateBuyer
from utils.utils import PermissionChecker



buyers_router = APIRouter()




@buyers_router.post("/buyers", response_model=Buyer)
async def create_buyer(
        body: CreateBuyer,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Закупщики": ["create"]}))
):
    created_obj = await BuyerDAO.add(session=db, **body.model_dump())
    db.commit()
    db.refresh(created_obj)
    return created_obj



@buyers_router.get("/buyers", response_model=List[Buyers])
async def get_buyer_list(
        name: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Закупщики": ["read"]}))
):
    filters = {}
    if name is not None:
        filters["name"] = name

    objs = await BuyerDAO.get_by_attributes(session=db, filters=filters if filters else None)
    return objs



@buyers_router.get("/buyers/{id}", response_model=Buyer)
async def get_buyer(
        id: UUID,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Закупщики": ["read"]}))
):
    obj = await BuyerDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    return obj



@buyers_router.put("/buyers", response_model=Buyer)
async def update_buyer(
        body: UpdateBuyer,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Закупщики": ["update"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    updated_obj = await BuyerDAO.update(session=db, data=body_dict)
    db.commit()
    db.refresh(updated_obj)
    return updated_obj



@buyers_router.delete("/buyers", response_model=List[Buyers])
async def delete_buyer(
        id: Optional[UUID],
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Закупщики": ["delete"]}))
):
    deleted_objs = await BuyerDAO.delete(session=db, filters={"id": id})
    db.commit()
    return deleted_objs

