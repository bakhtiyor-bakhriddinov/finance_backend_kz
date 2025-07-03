from datetime import datetime, date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import coalesce

from core.session import get_db
from dal.dao import RequestDAO, UserDAO, ClientDAO
from schemas.requests import Requests
from utils.utils import PermissionChecker



accounting_router = APIRouter()



@accounting_router.get("/purchase", response_model=Page[Requests])
async def get_purchase_requests(
        number: Optional[int] = None,
        client: Optional[str] = None,
        department_id: Optional[UUID] = None,
        supplier: Optional[str] = None,
        expense_type_id: Optional[UUID] = None,
        payment_type_id: Optional[UUID] = None,
        payment_sum: Optional[float] = None,
        sap_code: Optional[str] = None,
        created_at: Optional[date] = None,
        payment_date: Optional[date] = None,
        status: Optional[str] = "1,2,3,5,6",
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Заявки": ["purchase requests"]}))
):
    filters = {k: v for k, v in locals().items() if v is not None and k not in ["db", "current_user"]}

    filters["purchase_approved"] = True

    if client is not None:
        query = await ClientDAO.get_all(session=db, filters={"fullname": client})
        clients = db.execute(query).scalars().all()
        filters["client_id"] = [client.id for client in clients]

    query = await RequestDAO.get_all(
        session=db,
        filters=filters if filters else None
    )
    result = db.execute(query.order_by(RequestDAO.model.number.desc())).scalars().all()
    return paginate(result)

