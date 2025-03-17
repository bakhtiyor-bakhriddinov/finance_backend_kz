from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.config import settings
from core.session import get_db
from dal.dao import RequestDAO, InvoiceDAO, ContractDAO, FileDAO, LogDAO
from schemas.requests import Requests, Request, UpdateRequest, CreateRequest
from utils.utils import PermissionChecker, send_telegram_message

requests_router = APIRouter()




@requests_router.post("/requests", response_model=Request)
async def create_request(
        body: CreateRequest,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Requests": ["create"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    body_dict.pop("file_paths", None)
    body_dict.pop("contract", None)
    created_request = await RequestDAO.add(session=db, **body_dict)

    if body.file_paths is not None and body.contract is not None:
        contract = await ContractDAO.add(session=db, **{"request_id": created_request.id})
        await FileDAO.add(
            session=db,
            **{
                "file_paths": body.file_paths,
                "contract_id": contract.id if contract is not None else None
            }
        )
    # create logs
    await LogDAO.add(
        session=db,
        **{
            "status": 0,
            "request_id": created_request.id,
            "user_id": current_user["id"]
        }
    )

    db.commit()
    db.refresh(created_request)
    return created_request



@requests_router.get("/requests", response_model=Page[Requests])
async def get_request_list(
        number: Optional[int] = None,
        client_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        expense_type_id: Optional[UUID] = None,
        payment_type_id: Optional[UUID] = None,
        payment_sum: Optional[float] = None,
        sap_code: Optional[str] = None,
        approved: Optional[bool] = None,
        created_at: Optional[date] = None,
        payment_date: Optional[date] = None,
        status: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Requests": ["read"]}))
):
    filters = {}
    if number is not None:
        filters["number"] = number
    if client_id is not None:
        filters["client_id"] = client_id
    if department_id is not None:
        filters["department_id"] = department_id
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

    # data = {
    #     "number": number,
    #     "client_id": client_id,
    #     "department_id": department_id,
    #     "expense_type_id": expense_type_id,
    #     "payment_type_id": payment_type_id,
    #     "sum": payment_sum,
    #     "sap_code": sap_code,
    #     "approved": approved,
    #     "created_at": created_at,
    #     "payment_time": payment_date,
    #     "status": status
    # }
    # filtered_data = {k: v for k, v in data.items() if v is not None}

    query = await RequestDAO.get_all(
        session=db,
        filters=filters if filters else None
    )
    result = db.execute(query.order_by(RequestDAO.model.number.desc())).scalars().all()
    return paginate(result)



@requests_router.get("/requests/{id}", response_model=Request)
async def get_request(
        id: UUID,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Requests": ["read"]}))
):
    obj = await RequestDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    return obj



@requests_router.put("/requests", response_model=Request)
async def update_request(
        body: UpdateRequest,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Requests": ["update"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    body_dict.pop("file_paths", None)
    body_dict.pop("invoice", None)
    request = await RequestDAO.get_by_attributes(session=db, filters={"id": body.id}, first=True)
    request_payment_time = request.payment_time
    updated_request = await RequestDAO.update(session=db, data=body_dict)

    db.commit()
    db.refresh(updated_request)

    if body.file_paths is not None and body.invoice is not None:
        invoice = None
        if body.invoice is not None:
            invoice = await InvoiceDAO.add(session=db, **{"request_id": updated_request.id})

        await FileDAO.add(
            session=db,
            **{
                "file_paths": body.file_paths,
                "invoice_id": invoice.id if invoice is not None else None
            }
        )

        db.commit()
        db.refresh(updated_request)

    if body.status is not None:
        # create logs
        await LogDAO.add(
            session=db,
            **{
                "status": body.status,
                "request_id": updated_request.id,
                "user_id": current_user["id"]
            }
        )
        db.commit()
        db.refresh(updated_request)

        message_text = ""
        inline_keyboard = None
        status = updated_request.status
        number = updated_request.number
        if status == 1: # Новый
            message_text = (f"Ваша заявка #{number}s принята со стороны  финансового отдела.\n"
                            f"Срок оплаты {updated_request.payment_time.strftime('%d.%m.%Y')}")
        elif status == 4: # Отменен
            message_text = (f"Ваша заявка #{number}s отменена по причине:\n"
                            f"{updated_request.comment}")
        elif status == 5: # Обработан
            message_text = (f"Оплата по вашей заявке #{number}s проведена.\n"
                            f"Документ оплаты: “квиток фото”")
            inline_keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": "Посмотреть фото",
                            "url": f"{settings.BASE_URL}{updated_request.invoice.file.file_paths if updated_request.invoice else ''}"
                        }
                    ]
                ]
            }

        send_telegram_message(chat_id=updated_request.client.tg_id, message_text=message_text, keyboard=inline_keyboard)

    if body.payment_time is not None and request_payment_time is not None:
        message_text = (f"Срок оплаты по вашей заявке {updated_request.number} изменен с "
                        f"{request_payment_time.strftime('%d.%m.%Y')} на "
                        f"{updated_request.payment_time.strftime('%d.%m.%Y')} по причине:\n"
                        f"“{updated_request.comment}”")
        send_telegram_message(chat_id=updated_request.client.tg_id, message_text=message_text)

    return updated_request
