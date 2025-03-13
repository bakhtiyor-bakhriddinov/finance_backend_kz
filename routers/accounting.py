from datetime import datetime, date

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
async def get_statistics(
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Requests": ["read"]}))
):
    filters = {
        "payment_type_id": "88a747c1-5616-437c-ac71-a02b30287ee8",
        "payment_time": None,
        "status": 4
    }

    query = await RequestDAO.get_all(
        session=db,
        filters=filters if filters else None
    )
    result = db.execute(query.order_by(RequestDAO.model.number.desc())).scalars().all()
    return paginate(result)

