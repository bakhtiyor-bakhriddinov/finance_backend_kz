import calendar
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
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
    existed_obj = await BudgetDAO.get_by_attributes(
        session=db,
        filters={
            "department_id": body.department_id,
            "expense_type_id": body.expense_type_id,
            "start_date": body.start_date,
            "finish_date": body.finish_date
        },
        first=True
    )
    if existed_obj:
        raise HTTPException(status_code=400, detail="Данный бюджет уже создан !")

    obj = await BudgetDAO.add(session=db, **body.model_dump())
    db.commit()
    db.refresh(obj)
    return obj



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
        budget = budget if budget is not None else 0
        obj.value = budget
        expense = (await BudgetDAO.get_filtered_budget_expense(
            session=db,
            department_id=department_id,
            expense_type_id=obj.expense_type_id,
            start_date=start_date,
            finish_date=finish_date
        ))[0]
        expense = -expense if expense is not None else 0
        obj.expense_value = expense
        balance = budget - expense
        obj.balance_value = balance
        delayed = (await BudgetDAO.get_budget_delayed_sum(
            session=db,
            department_id=department_id,
            expense_type_id=obj.expense_type_id,
            start_date=start_date,
            finish_date=finish_date
        ))[0]
        obj.delayed = -delayed if delayed is not None else 0

    return objs



@budgets_router.get("/budget-balance", response_model=Budget)
async def get_budget_balance(
        department_id: UUID,
        expense_type_id: UUID,
        start_date: Optional[date] = None,
        finish_date: Optional[date] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Бюджеты": ["read"]}))
):
    filters = {
        "department_id": department_id,
        "expense_type_id": expense_type_id
    }
    if start_date is not None:
        filters["start_date"] = start_date.replace(day=1)
    if finish_date is not None:
        filters["finish_date"] = finish_date.replace(day=calendar.monthrange(finish_date.year, finish_date.month)[1])

    current_date = date.today()
    obj = await BudgetDAO.get_by_attributes(session=db, filters=filters, first=True)
    if not obj:
        raise HTTPException(status_code=400, detail="По указанным промежуткам дат баланс бюджета не найден !")

    budget = (await BudgetDAO.get_filtered_budget_sum(
        session=db,
        department_id=department_id,
        expense_type_id=expense_type_id,
        start_date=current_date if start_date is None else start_date,
        finish_date=current_date if finish_date is None else finish_date
    ))[0]
    budget = budget if budget is not None else 0
    expense = (await BudgetDAO.get_filtered_budget_expense(
        session=db,
        department_id=department_id,
        expense_type_id=expense_type_id,
        start_date=current_date if start_date is None else start_date,
        finish_date=current_date if finish_date is None else finish_date
    ))[0]
    expense = -expense if expense is not None else 0
    obj.value = budget - expense

    return obj



@budgets_router.get("/calendar-budgets")
async def get_calendar_balance(
        department_id: UUID,
        expense_type_id: UUID,
        created_date: Optional[date],
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Бюджеты": ["read"]}))
):
    budget = await BudgetDAO.get_budget_by_attributes(session=db, department_id=department_id, expense_type_id=expense_type_id, created_date=created_date)
    start_date = budget.start_date
    finish_date = budget.finish_date
    difference = finish_date - start_date
    days = difference.days + 1
    if days > 1:
        pass
    budget_details = await BudgetDAO.get_calendar_budget_details(
        session=db,
        start_date=start_date,
        finish_date=finish_date,
        budget_id=budget.id,
        department_id=department_id,
        expense_type_id=expense_type_id,
        days=days
    )

    data = [row._asdict() for row in budget_details]

    return data
