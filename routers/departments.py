from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from sqlalchemy.ext.asyncio import AsyncSession

from core.session import get_db
from dal.dao import DepartmentDAO
from schemas.departments import Department, CreateDepartment, Departments, UpdateDepartment
from utils.utils import PermissionChecker

departments_router = APIRouter()



@departments_router.post("/departments", response_model=Department)
async def create_department(
        body: CreateDepartment,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Departments": ["create"]}))
):
    created_department = await DepartmentDAO.add(session=db, **body.model_dump())
    await db.commit()
    await db.refresh(created_department)
    return created_department


@departments_router.get("/departments", response_model=Page[Departments])
async def get_department_list(
        name: Optional[str] = None,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Departments": ["read"]}))
):
    filters = {}
    if name is not None:
        filters["name"] = name
    # filtered_data = {k: v for k, v in data.items() if v is not None}
    departments = await DepartmentDAO.get_all(session=db, filters=filters)
    return paginate(departments)


@departments_router.get("/departments/{id}", response_model=Department)
async def get_department(
        id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Departments": ["read"]}))
):
    department = await DepartmentDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    return department


@departments_router.put("/departments", response_model=Department)
async def update_department(
        body: UpdateDepartment,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Departments": ["update"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    updated_department = await DepartmentDAO.update(session=db, data=body_dict)
    await db.commit()
    await db.refresh(updated_department)
    return updated_department


@departments_router.delete("/departments", response_model=List[Departments])
async def delete_department(
        id: Optional[UUID],
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Departments": ["delete"]}))
):
    deleted_departments = await DepartmentDAO.delete(session=db, filters={"id": id})
    await db.commit()
    return deleted_departments

