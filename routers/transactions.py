from collections import defaultdict
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi_pagination import Page, paginate
from requests import session
from sqlalchemy.orm import Session

from core.session import get_db
from dal.dao import TransactionDAO, DepartmentDAO
from schemas.transactions import Transaction, CreateTransaction, Transactions, DepartmentTransactions
from utils.utils import PermissionChecker



transactions_router = APIRouter()




@transactions_router.post("/transactions", response_model=Transaction)
async def create_transaction(
        body: CreateTransaction,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Транзакции": ["create"]}))
):
    body_dict = body.model_dump(exclude_none=True)

    if body.value > 0:
        body_dict["is_income"] = True
    else:
        body_dict["is_income"] = False

    created_obj = await TransactionDAO.add(session=db, **body_dict)
    db.commit()
    db.refresh(created_obj)
    return created_obj




@transactions_router.get("/department-transactions", response_model=DepartmentTransactions)
async def get_department_transaction_list(
        department_id: Optional[UUID],
        start_date: Optional[date] = None,
        finish_date: Optional[date] = None,
        page: Optional[int] = Query(1, ge=1, description="Page number for transactions"),
        size: Optional[int] = Query(50, ge=1, le=100, description="Number of transactions per page"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Транзакции": ["read"]}))
):
    department = await DepartmentDAO.get_by_attributes(session=db, filters={"id": department_id}, first=True)
    transactions = await TransactionDAO.get_department_transactions(
        session=db,
        department_id=department_id,
        start_date=start_date,
        finish_date=finish_date,
        page=page,
        size=size
    )
    for transaction in transactions:
        if transaction.budget is not None:
            transaction.currency = "Сум"

    total_transactions = await TransactionDAO.get_department_all_transactions(
        session=db,
        department_id=department_id,
        start_date=start_date,
        finish_date=finish_date
    )
    pages = (total_transactions + size - 1) // size  # Ceiling division for pages
    data_dict = {
        "department": department,
        "transactions": {
            "page": page,
            "size": size,
            "pages": pages,
            "total": total_transactions,
            "items": transactions
        }
    }

    return data_dict



@transactions_router.get("/budget-transactions", response_model=List[Transactions])
async def get_budget_transaction_list(
        budget_id: Optional[UUID],
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Транзакции": ["read"]}))
):
    transactions = await TransactionDAO.get_budget_transactions(
        session=db,
        budget_id=budget_id
    )
    for transaction in transactions:
        transaction.currency = "Сум"
    return transactions



@transactions_router.get("/calendar-transactions")
async def get_calendar_transaction_list(
        start_date: Optional[date] = None,
        finish_date: Optional[date] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Транзакции": ["read"]}))
):
    result = await TransactionDAO.get_calendar_transactions(
        session=db,
        start_date=start_date,
        finish_date=finish_date
    )
    # print(result)

    # Process results into the required structure
    # grouped_data = defaultdict(lambda: {"transactions": {}, "total": 0})
    #
    # for date, payment_type, total_value in result:
    #     date_str = str(date)  # Convert date to string
    #     grouped_data[date_str]["transactions"][payment_type] = float(total_value)  # Convert Decimal to int
    #     grouped_data[date_str]["total"] += float(total_value)  # Update total sum
    #
    # # Convert to the expected list format
    # return [{date: data["transactions"], "total": data["total"]} for date, data in grouped_data.items()]

    grouped_data = defaultdict(lambda: {"total": 0})  # Default structure for each date

    for date, payment_type, total_value in result:
        date_str = str(date)  # Convert date to string
        grouped_data[date_str][payment_type] = int(total_value)  # Store transaction
        grouped_data[date_str]["total"] += int(total_value)  # Update total

    # Wrap the entire dictionary inside a list as required
    return grouped_data


