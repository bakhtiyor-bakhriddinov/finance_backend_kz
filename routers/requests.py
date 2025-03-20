from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.config import settings
from core.session import get_db
from dal.dao import RequestDAO, InvoiceDAO, ContractDAO, FileDAO, LogDAO
from schemas.requests import Requests, Request, UpdateRequest, CreateRequest
from utils.utils import PermissionChecker, send_telegram_message, send_telegram_document

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
    if body.status == 4:
        if "reject" not in current_user["permissions"]["Requests"]:
            body_dict.pop("status", None)
            body_dict.pop("comment", None)
            raise HTTPException(status_code=404, detail="У вас нет прав отменить статус заявки !")

    if body.approved is True:
        if "approve" not in current_user["permissions"]["Requests"]:
            body_dict.pop("approved", None)
            body_dict.pop("approve_comment", None)
            raise HTTPException(status_code=404, detail="У вас нет прав одобрить заявку !")

    if body.to_accounting is True:
        if request.payment_type_id != "88a747c1-5616-437c-ac71-a02b30287ee8":
            body_dict.pop("to_accounting", None)
            raise HTTPException(status_code=404, detail="Тип оплаты не является перечислением !")

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
        chat_id = updated_request.client.tg_id
        inline_keyboard = None
        request_text = (
            f"📌 Заявка #{request.number}s\n\n"
            f"📅 Дата заявки: {datetime.strptime(request.created_at, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%d.%m.%Y')}\n"
            f"📍 Отдел: {request.department.name}\n"
            f"👤 Заказчик: {request.client.fullname}\n"
            f"📞 Номер заказчика: {request.client.phone}\n"
            f"🛒 Закупщик: {request.buyer}\n"
            f"💰 Тип затраты: {request.expense_type.name}\n"
            f"🏢 Поставщик: {request.supplier}\n\n"
            f"💲 Стоимость: {int(request.sum)} сум\n"
            f"💵 Валюта: {request.currency}\n"
            f"💳 Тип оплаты: {request.payment_type.name}\n"
            f"💳 Карта перевода: {request.payment_card if request.payment_card is not None else ''}\n"
            f"📜 № Заявки в SAP: {request.sap_code}\n\n"
            f"📝 Комментарии: {request.description}\n\n"
            f"📃 Документ оплаты 👇"
        )
        status = updated_request.status
        number = updated_request.number
        if status == 1: # Принят
            if request.payment_type_id == "822e49f7-f54e-481e-997d-e4cb81b061e1":
                chat_id = settings.CHAT_GROUP  # chat id of group
                try:
                    send_telegram_message(chat_id=chat_id, message_text=request_text, keyboard=inline_keyboard)
                except Exception as e:
                    print("Sending Error: ", e)

            message_text = (f"Ваша заявка #{number}s принята со стороны  финансового отдела.\n"
                            f"Срок оплаты {updated_request.payment_time.strftime('%d.%m.%Y')}")
            send_telegram_message(chat_id=chat_id, message_text=message_text, keyboard=inline_keyboard)

        elif status == 4: # Отменен
            message_text = (f"Ваша заявка #{number}s отменена по причине:\n"
                            f"{updated_request.comment}")
            send_telegram_message(chat_id=chat_id, message_text=message_text, keyboard=inline_keyboard)

        elif status == 5: # Обработан
            # inline_keyboard = {
            #     "inline_keyboard": [
            #         [
            #             {
            #                 "text": f"Посмотреть фото №{i+1}",
            #                 "url": f"{settings.BASE_URL}/{file_path if updated_request.invoice else ''}"
            #             } for i, file_path in enumerate(file.file_paths)
            #         ] for file in updated_request.invoice.file
            #     ]
            # }
            try:
                send_telegram_message(chat_id=chat_id, message_text=request_text, keyboard=inline_keyboard)
                file_paths = updated_request.invoice.file.file_paths if updated_request.invoice else None
                if file_paths is not None:
                    for file_path in file_paths:
                        send_telegram_document(chat_id=updated_request.client.tg_id, file_path=file_path)
            except Exception as e:
                print("Sending Error: ", e)

    if body.payment_time is not None and request_payment_time is not None:
        message_text = (f"Срок оплаты по вашей заявке {updated_request.number} изменен с "
                        f"{request_payment_time.strftime('%d.%m.%Y')} на "
                        f"{updated_request.payment_time.strftime('%d.%m.%Y')} по причине:\n"
                        f"“{updated_request.comment}”")
        try:
            send_telegram_message(chat_id=updated_request.client.tg_id, message_text=message_text)
        except Exception as e:
            print("Sending Error: ", e)

    return updated_request
