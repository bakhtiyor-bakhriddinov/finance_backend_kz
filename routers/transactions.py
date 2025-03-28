from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
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
    body_dict = body.model_dump(exclude_none=True)

    if body.value > 0:
        body_dict["is_income"] = True
    else:
        body_dict["is_income"] = False

    created_obj = await TransactionDAO.add(session=db, **body_dict)
    db.commit()
    db.refresh(created_obj)
    return created_obj




@transactions_router.get("/transactions", response_model=Page[Transactions])
async def get_transaction_list(
        department_id: Optional[UUID],
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Transactions": ["read"]}))
):

    objs = await TransactionDAO.get_department_transactions(session=db, department_id=department_id)
    return paginate(objs)

