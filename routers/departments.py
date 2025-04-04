from collections import defaultdict
from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, paginate
from sqlalchemy.orm import Session

from core.session import get_db
from dal.dao import DepartmentDAO, UserDAO, TransactionDAO
from schemas.departments import Department, CreateDepartment, Departments, UpdateDepartment
from utils.utils import PermissionChecker

departments_router = APIRouter()



@departments_router.post("/departments", response_model=Department)
async def create_department(
        body: CreateDepartment,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Departments": ["create"]}))
):
    created_department = await DepartmentDAO.add(session=db, **body.model_dump())
    db.commit()
    db.refresh(created_department)
    return created_department


@departments_router.get("/departments", response_model=Page[Departments])
async def get_department_list(
        name: Optional[str] = None,
        start_date: Optional[date] = None,
        finish_date: Optional[date] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Departments": ["read", "accounting"]}))
):
    filters = {}
    if name is not None:
        filters["name"] = name

    departments = await DepartmentDAO.get_by_attributes(session=db, filters=filters if filters else None)
    user = await UserDAO.get_by_attributes(session=db, filters={"id": current_user["id"]}, first=True)
    role_department_relations = user.role.roles_departments
    role_departments = [relation.department_id for relation in role_department_relations]
    departments = [department for department in departments if department.id in role_departments] if role_departments else [department for department in departments]
    for department in departments:
        budget = (
            await DepartmentDAO.get_department_total_budget(
                session=db, department_id=department.id, start_date=start_date, finish_date=finish_date
            )
        )[0]
        department.total_budget = budget
        # print("total_budget: ", budget)

    return paginate(departments)


@departments_router.get("/departments/{id}", response_model=Department)
async def get_department(
        id: UUID,
        start_date: date,
        finish_date: date,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Departments": ["read"]}))
):
    department = await DepartmentDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    budget = await DepartmentDAO.get_department_monthly_budget(session=db, department_id=id, start_date=start_date, finish_date=finish_date)

    # Group data by year
    # result_dict = defaultdict(dict)
    result_dict = defaultdict(lambda: defaultdict(lambda: {"budget": 0.0, "expense": 0.0, "pending": 0.0, "balance": 0.0, "pending_requests": 0}))
    # print("budget: ", budget)

    for year, month, type, sum, pending_requests in budget:
        result_dict[int(year)][int(month)][type] = -float(sum) if type == "expense" or type == "pending" else float(sum)
        result_dict[int(year)][int(month)]["balance"] = result_dict[int(year)][int(month)]["budget"] - result_dict[int(year)][int(month)]["expense"]
        result_dict[int(year)][int(month)]["pending_requests"] = pending_requests

    # Convert defaultdict to a list of dictionaries
    department.monthly_budget = [{year: dict(months)} for year, months in result_dict.items()]
    # print(department.monthly_budget)

    return department


@departments_router.put("/departments", response_model=Department)
async def update_department(
        body: UpdateDepartment,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Departments": ["update"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    updated_department = await DepartmentDAO.update(session=db, data=body_dict)
    db.commit()
    db.refresh(updated_department)
    return updated_department


@departments_router.delete("/departments")
async def delete_department(
        id: Optional[UUID],
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Departments": ["delete"]}))
):
    deleted_department = await DepartmentDAO.delete(session=db, filters={"id": id})
    # db.commit()
    if deleted_department is True:
        return {"Message": "Отдел удален успешно !"}
    else:
        raise HTTPException(status_code=400, detail="Данный отдел не найден !")
