from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.session import get_db
from dal.dao import BudgetDAO
from schemas.budgets import Budgets, CreateBudget, Budget
from utils.utils import PermissionChecker

budgets_router = APIRouter()




@budgets_router.post("/budgets", response_model=Budget)
async def create_budget(
        body: CreateBudget,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Бюджеты": ["create"]}))
):
    created_obj = await BudgetDAO.add(session=db, **body.model_dump())
    db.commit()
    db.refresh(created_obj)
    return created_obj



@budgets_router.get("/budgets", response_model=List[Budgets])
async def get_budget_list(
        department_id: UUID,
        start_date: date,
        finish_date: date,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Бюджеты": ["read"]}))
):
    filters = {
        "department_id": department_id,
        "start_date": start_date,
        "finish_date": finish_date
    }
    objs = await BudgetDAO.get_by_attributes(session=db, filters=filters)
    for obj in objs:
        budget = (await BudgetDAO.get_budget_sum(session=db, budget_id=obj.id))[0]
        obj.value = budget

    return objs



@budgets_router.get("/budget-balance", response_model=Budget)
async def get_budget_balance(
        department_id: UUID,
        expense_type_id: UUID,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Бюджеты": ["read"]}))
):
    filters = {
        "department_id": department_id,
        "expense_type_id": expense_type_id
    }
    current_date = date.today()
    obj = await BudgetDAO.get_by_attributes(session=db, filters=filters, first=True)
    budget = (await BudgetDAO.get_filtered_budget_sum(
        session=db,
        department_id=department_id,
        expense_type_id=expense_type_id,
        current_date=current_date
    ))[0]
    budget = budget if budget is not None else 0
    # print("budget: ", budget)
    expense = (await BudgetDAO.get_filtered_budget_expense(
        session=db,
        department_id=department_id,
        expense_type_id=expense_type_id,
        current_date=current_date
    ))[0]
    # print("expense: ", expense)
    expense = -expense if expense is not None else 0
    obj.value = budget - expense

    return obj



