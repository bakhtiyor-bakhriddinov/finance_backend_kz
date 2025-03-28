from datetime import datetime, date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import coalesce

from core.session import get_db
from dal.dao import RequestDAO
from schemas.requests import Requests
from utils.utils import PermissionChecker



accounting_router = APIRouter()



@accounting_router.get("/accounting", response_model=Page[Requests])
async def get_accounting(
        number: Optional[int] = None,
        client_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        supplier: Optional[str] = None,
        expense_type_id: Optional[UUID] = None,
        payment_type_id: Optional[UUID] = None,
        payment_sum: Optional[float] = None,
        sap_code: Optional[str] = None,
        approved: Optional[bool] = None,
        created_at: Optional[date] = None,
        payment_date: Optional[date] = None,
        status: Optional[str] = "1,2,3,5",
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Requests": ["accounting"]}))
):
    filters = {}
    if number is not None:
        filters["number"] = number
    if client_id is not None:
        filters["client_id"] = client_id
    if department_id is not None:
        filters["department_id"] = department_id
    if supplier is not None:
        filters["supplier"] = supplier
    if expense_type_id is not None:
        filters["expense_type_id"] = expense_type_id
    if payment_type_id is not None:
        filters["payment_type_id"] = payment_type_id
    if payment_sum is not None:
        filters["sum"] = payment_sum
    if sap_code is not None:
        filters["sap_code"] = sap_code
    if approved is not None:
        filters["approved"] = approved
    if created_at is not None:
        filters["created_at"] = created_at
    if payment_date is not None:
        filters["payment_time"] = payment_date
    if status is not None:
        filters["status"] = status

    filters["payment_type_id"] = UUID("88a747c1-5616-437c-ac71-a02b30287ee8")
    filters["payment_time"] = None
    filters["to_accounting"] = True

    # filters = {
    #     "payment_type_id": UUID("88a747c1-5616-437c-ac71-a02b30287ee8"),
    #     "payment_time": None,
    #     "status": [1, 2, 3, 5],
    #     "to_accounting": True
    # }

    query = await RequestDAO.get_all(
        session=db,
        filters=filters if filters else None
    )
    result = db.execute(query.order_by(RequestDAO.model.number.desc())).scalars().all()
    return paginate(result)

