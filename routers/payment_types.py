from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.session import get_db
from dal.dao import PaymentTypeDAO
from schemas.payment_types import PaymentType, CreatePaymentType, PaymentTypes, UpdatePaymentType
from utils.utils import PermissionChecker


payment_types_router = APIRouter()



@payment_types_router.post("/payment-types", response_model=PaymentType)
async def create_payment_type(
        body: CreatePaymentType,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Типы оплаты": ["create"]}))
):
    created_obj = await PaymentTypeDAO.add(session=db, **body.model_dump())
    db.commit()
    db.refresh(created_obj)
    return created_obj


@payment_types_router.get("/payment-types", response_model=List[PaymentTypes])
async def get_payment_type_list(
        name: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Типы оплаты": ["read", "accounting", "transfer", "list"]}))
):
    filters = {}
    if name is not None:
        filters["name"] = name

    objs = await PaymentTypeDAO.get_by_attributes(session=db, filters=filters if filters else None)
    return objs


@payment_types_router.get("/payment-types/{id}", response_model=PaymentType)
async def get_payment_type(
        id: UUID,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Типы оплаты": ["read"]}))
):
    obj = await PaymentTypeDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    return obj


@payment_types_router.put("/payment-types", response_model=PaymentType)
async def update_payment_type(
        body: UpdatePaymentType,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Типы оплаты": ["update"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    updated_obj = await PaymentTypeDAO.update(session=db, data=body_dict)
    db.commit()
    db.refresh(updated_obj)
    return updated_obj


@payment_types_router.delete("/payment-types", response_model=List[PaymentTypes])
async def delete_payment_type(
        id: Optional[UUID],
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Типы оплаты": ["delete"]}))
):
    deleted_objs = await PaymentTypeDAO.delete(session=db, filters={"id": id})
    db.commit()
    return deleted_objs

