from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from sqlalchemy.orm import Session

from core.session import get_db
from dal.dao import RequestDAO, ClientDAO, DepartmentDAO, ExpenseTypeDAO
from schemas.requests import Requests
from utils.utils import PermissionChecker

checker_router = APIRouter()



@checker_router.get("/financier-checks", response_model=Page[Requests])
async def get_unchecked_requests(
        number: Optional[int] = None,
        client: Optional[str] = None,
        department_id: Optional[UUID] = None,
        supplier: Optional[str] = None,
        expense_type_id: Optional[UUID] = None,
        payment_type_id: Optional[UUID] = None,
        payment_sum: Optional[float] = None,
        sap_code: Optional[str] = None,
        purchase_approved: Optional[bool] = None,
        checked_by_financier: bool = False,
        created_at: Optional[date] = None,
        payment_date: Optional[date] = None,
        status: Optional[str] = "0,1,2,3,4,5,6",
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Заявки": ["checkable requests"]}))
):
    filters = {k: v for k, v in locals().items() if v is not None and k not in ["db", "current_user"]}

    if expense_type_id is None:
        expense_types = await ExpenseTypeDAO.get_by_attributes(session=db, filters={"checkable": True})
        filters["expense_type_id"] = [expense_type.id for expense_type in expense_types]

    if client is not None:
        clients = await ClientDAO.get_by_attributes(session=db, filters={"fullname": client})
        filters["client_id"] = [client.id for client in clients]

    query = await RequestDAO.get_all(
        session=db,
        filters=filters if filters else None
    )
    if query is None:
        return paginate([])

    result = db.execute(query.order_by(RequestDAO.model.number.desc())).scalars().all()
    return paginate(result)

