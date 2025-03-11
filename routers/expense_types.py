from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from sqlalchemy.ext.asyncio import AsyncSession

from core.session import get_db
from dal.dao import ExpenseTypeDAO
from schemas.departments import Department, CreateDepartment, Departments, UpdateDepartment
from schemas.expense_types import CreateExpenseType, ExpenseType, ExpenseTypes, UpdateExpenseType
from utils.utils import PermissionChecker


expense_types_router = APIRouter()



@expense_types_router.post("/expense-types", response_model=ExpenseType)
async def create_expense_type(
        body: CreateExpenseType,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"ExpenseTypes": ["create"]}))
):
    created_obj = await ExpenseTypeDAO.add(session=db, **body.model_dump())
    await db.commit()
    await db.refresh(created_obj)
    return created_obj


@expense_types_router.get("/expense-types", response_model=List[ExpenseTypes])
async def get_expense_type_list(
        name: Optional[str] = None,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"ExpenseTypes": ["read"]}))
):
    # data = {
    #     "name": name
    # }
    # filtered_data = {k: v for k, v in data.items() if v is not None}
    objs = await ExpenseTypeDAO.get_all(session=db)
    return objs


@expense_types_router.get("/expense-types/{id}", response_model=ExpenseType)
async def get_expense_type(
        id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"ExpenseTypes": ["read"]}))
):
    obj = await ExpenseTypeDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    return obj


@expense_types_router.put("/expense-types", response_model=ExpenseType)
async def update_expense_type(
        body: UpdateExpenseType,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"ExpenseTypes": ["update"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    updated_obj = await ExpenseTypeDAO.update(session=db, data=body_dict)
    await db.commit()
    await db.refresh(updated_obj)
    return updated_obj


@expense_types_router.delete("/expense-types", response_model=List[ExpenseTypes])
async def delete_expense_type(
        id: Optional[UUID],
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"ExpenseTypes": ["delete"]}))
):
    deleted_objs = await ExpenseTypeDAO.delete(session=db, filters={"id": id})
    await db.commit()
    return deleted_objs

