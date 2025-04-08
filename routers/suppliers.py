from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.session import get_db
from dal.dao import SupplierDAO
from schemas.suppliers import Suppliers, Supplier, CreateSupplier, UpdateSupplier
from utils.utils import PermissionChecker



suppliers_router = APIRouter()




@suppliers_router.post("/suppliers", response_model=Supplier)
async def create_supplier(
        body: CreateSupplier,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Поставщики": ["create"]}))
):
    created_obj = await SupplierDAO.add(session=db, **body.model_dump())
    db.commit()
    db.refresh(created_obj)
    return created_obj



@suppliers_router.get("/suppliers", response_model=List[Suppliers])
async def get_supplier_list(
        name: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Поставщики": ["read"]}))
):
    filters = {}
    if name is not None:
        filters["name"] = name
    objs = await SupplierDAO.get_by_attributes(session=db, filters=filters if filters else None)
    return objs



@suppliers_router.get("/suppliers/{id}", response_model=Supplier)
async def get_supplier(
        id: UUID,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Поставщики": ["read"]}))
):
    obj = await SupplierDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    return obj



@suppliers_router.put("/suppliers", response_model=Supplier)
async def update_supplier(
        body: UpdateSupplier,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Поставщики": ["update"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    updated_obj = await SupplierDAO.update(session=db, data=body_dict)
    db.commit()
    db.refresh(updated_obj)
    return updated_obj



@suppliers_router.delete("/suppliers", response_model=List[Suppliers])
async def delete_supplier(
        id: Optional[UUID],
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Поставщики": ["delete"]}))
):
    deleted_objs = await SupplierDAO.delete(session=db, filters={"id": id})
    db.commit()
    return deleted_objs

