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




transfers_router = APIRouter()



@transfers_router.get("/transfers", response_model=Page[Requests])
async def get_transfers(
        number: Optional[int] = None,
        client: Optional[str] = None,
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
        current_user: dict = Depends(PermissionChecker(required_permissions={"Заявки": ["transfer"]}))
):
    filters = {}
    if number is not None:
        filters["number"] = number
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

    filters["payment_type_id"] = UUID('eda54dd2-2eef-430e-ae4e-0c4d68a44298')
    filters["to_transfer"] = True
    if filters.get("payment_time", None) is None:
        filters["payment_time"] = None

    if client is not None:
        query = await ClientDAO.get_all(session=db, filters={"fullname": client})
        clients = db.execute(query).scalars().all()
        filters["client_id"] = [client.id for client in clients]

    if filters.get("department_id", None) is None:
        user = await UserDAO.get_by_attributes(session=db, filters={"id": current_user["id"]}, first=True)
        role_department_relations = user.role.roles_departments
        role_departments = [relation.department_id for relation in role_department_relations]
        filters["department_id"] = role_departments

    query = await RequestDAO.get_all(
        session=db,
        filters=filters if filters else None
    )
    result = db.execute(query.order_by(RequestDAO.model.number.desc())).scalars().all()
    return paginate(result)

