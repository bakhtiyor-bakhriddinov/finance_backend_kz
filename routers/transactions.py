from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.session import get_db
from dal.dao import TransactionDAO
from schemas.transactions import Transaction, CreateTransaction, Transactions
from utils.utils import PermissionChecker



transactions_router = APIRouter()




@transactions_router.post("/transactions", response_model=Transaction)
async def create_transaction(
        body: CreateTransaction,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Transactions": ["create"]}))
):
    if body.value > 0:
        body.is_income = True
    else:
        body.is_income = False

    created_obj = await TransactionDAO.add(session=db, **body.model_dump())
    db.commit()
    db.refresh(created_obj)
    return created_obj




# @transactions_router.get("/transactions", response_model=List[Transactions])
# async def get_transaction_list(
#         budget_id: Optional[UUID] = None,
#         request_id: Optional[UUID] = None,
#         status: Optional[int] = None,
#         db: Session = Depends(get_db),
#         current_user: dict = Depends(PermissionChecker(required_permissions={"Transactions": ["read"]}))
# ):
#     filters = {}
#     if budget_id is not None:
#         filters["budget_id"] = budget_id
#     if request_id is not None:
#         filters["request_id"] = request_id
#     if status is not None:
#         filters["status"] = status
#
#     objs = await TransactionDAO.get_by_attributes(session=db, filters=filters)
#     for obj in objs:
#         budget = (await BudgetDAO.get_budget_sum(session=db, budget_id=obj.id))[0]
#         obj.value = budget
#
#     return objs





