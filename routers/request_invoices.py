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


invoice_router = APIRouter()



@invoice_router.get("/requests-invoices", response_model=Page[Requests])
async def get_requests_with_invoices(
        number: Optional[int] = None,
        contract_number: Optional[str] = None,
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
        current_user: dict = Depends(PermissionChecker(required_permissions={"Заявки": ["requests_with_receipts"]}))
):
    filters = {k: v for k, v in locals().items() if v is not None and k not in ["db", "current_user"]}

    if client is not None:
        clients = await ClientDAO.get_by_attributes(session=db, filters={"fullname": client})
        filters["client_id"] = [client.id for client in clients]

    query = await RequestDAO.get_all(
        session=db,
        filters=filters if filters else None
    )
    if query is None:
        return paginate([])

    if contract_number is None:
        result = db.execute(
            query
            .filter(RequestDAO.model.contract_number.isnot(None))
            .order_by(RequestDAO.model.number.desc())
        ).scalars().all()
    else:
        result = db.execute(query.order_by(RequestDAO.model.number.desc())).scalars().all()

    return paginate(result)

