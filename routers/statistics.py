from datetime import datetime, date

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import coalesce

from core.session import get_db
from dal.dao import RequestDAO
from utils.utils import PermissionChecker


statistics_router = APIRouter()




@statistics_router.get("/statistics")
async def get_statistics(
        start_date: date,
        finish_date: date,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Requests": ["statistics"]}))
):
    requests_statuses = db.query(
        RequestDAO.model.status, func.count(RequestDAO.model.id)
    ).filter(
        RequestDAO.model.created_at.between(start_date, finish_date)
    ).group_by(
        RequestDAO.model.status
    ).all()
    # print("requests_statuses: ", requests_statuses)

    today_paying_requests = db.query(
        func.count(RequestDAO.model.id)
    ).filter(
        and_(
            RequestDAO.model.status == 2,
            func.date(RequestDAO.model.payment_time) == datetime.now().date()
        )
    ).all()
    # print("today_paying_requests: ", today_paying_requests)

    expense_statistics = db.query(
        coalesce(func.sum(RequestDAO.model.sum), 0)
    ).filter(
        and_(
            RequestDAO.model.status == 5,
            RequestDAO.model.created_at.between(start_date, finish_date)
        )
    ).all()
    # print("expense_statistics: ", expense_statistics)

    data = {
        "request_statuses": {status: count for status, count in requests_statuses},
        "requests_to_pay": today_paying_requests[0][0],
        "expense_statistics": expense_statistics[0][0],
    }
    return data
