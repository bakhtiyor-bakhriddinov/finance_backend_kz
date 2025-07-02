from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.session import get_db
from dal.dao import ClientDAO, DepartmentDAO
from schemas.clients import Clients, Client, UpdateClient, CreateClient
from utils.utils import PermissionChecker



clients_router = APIRouter()


@clients_router.post("/clients", response_model=Client)
async def create_client(
        body: CreateClient,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Клиенты": ["create"]}))
):
    obj = await ClientDAO.add(session=db, **body.model_dump())
    db.commit()
    db.refresh(obj)
    return obj


@clients_router.get("/clients", response_model=Page[Clients])
async def get_client_list(
        fullname: Optional[str] = None,
        phone: Optional[str] = None,
        tg_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Клиенты": ["read", "accounting"]}))
):
    filters = {}
    if fullname is not None:
        filters["fullname"] = fullname
    if phone is not None:
        filters["phone"] = phone
    if tg_id is not None:
        filters["tg_id"] = tg_id
    if is_active is not None:
        filters["is_active"] = is_active

    query = await ClientDAO.get_all(session=db, filters=filters if filters else None)
    result = db.execute(query).scalars().all()
    return paginate(result)



@clients_router.get("/clients/{id}", response_model=Client)
async def get_client(
        id: UUID,
        start_date: Optional[date] = None,
        finish_date: Optional[date] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Клиенты": ["read"]}))
):
    obj = await ClientDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    if start_date is not None and finish_date is not None:
        departments = obj.department
        for department in departments:
            budget = (
                await DepartmentDAO.get_department_total_budget(
                    session=db, department_id=department.id, start_date=start_date, finish_date=finish_date, payment_date=None
                )
            )[0]
            department.total_budget = budget

    return obj



@clients_router.put("/clients", response_model=Client)
async def update_client(
        body: UpdateClient,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Клиенты": ["update"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    updated_obj = await ClientDAO.update(session=db, data=body_dict)
    db.commit()
    db.refresh(updated_obj)
    return updated_obj


