from datetime import datetime, date, timedelta
from typing import Optional, List
from uuid import UUID

import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, paginate
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.config import settings
from core.session import get_db
from dal.dao import (
    RequestDAO,
    InvoiceDAO,
    ContractDAO,
    FileDAO,
    LogDAO,
    TransactionDAO,
    UserDAO,
    ClientDAO,
    BudgetDAO,
    DepartmentDAO,
    ExpenseTypeDAO
)
from schemas.requests import Requests, Request, UpdateRequest, CreateRequest, GenerateExcel
from utils.utils import PermissionChecker, send_telegram_message, send_telegram_document, error_sender, excel_generator



requests_router = APIRouter()




@requests_router.post("/requests", response_model=Request)
async def create_request(
        body: CreateRequest,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Заявки": ["create"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    body_dict.pop("file_paths", None)
    body_dict.pop("contract", None)

    if body.client_id is None:
        body_dict["user_id"] = current_user.get("id")

    if not body_dict.get("status"):
        body_dict["status"] = 0

    if not body_dict.get("purchase_approved"):
        department = await DepartmentDAO.get_by_attributes(session=db, filters={"id": body.department_id}, first=True)
        expense_type = await ExpenseTypeDAO.get_by_attributes(session=db, filters={"id": body.expense_type_id}, first=True)
        if department.purchasable is True and expense_type.purchasable is True:
            body_dict["purchase_approved"] = False

    if not body_dict.get("checked_by_financier"):
        expense_type = await ExpenseTypeDAO.get_by_attributes(session=db, filters={"id": body.expense_type_id}, first=True)
        if expense_type.checkable is True:
            body_dict["checked_by_financier"] = False

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
            "sum": created_request.sum,
            "currency": created_request.currency,
            "status": 0,
            "request_id": created_request.id,
            "user_id": current_user["id"]
        }
    )

    await TransactionDAO.add(
        session=db,
        **{
            "request_id": created_request.id,
            "status": 0,
            "value": -created_request.sum,
            "is_income": False
        }
    )

    db.commit()
    db.refresh(created_request)
    return created_request



@requests_router.get("/requests", response_model=Page[Requests])
async def get_request_list(
        number: Optional[int] = None,
        client: Optional[str] = None,
        client_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        supplier: Optional[str] = None,
        expense_type_id: Optional[UUID] = None,
        payment_type_id: Optional[UUID] = None,
        payment_sum: Optional[float] = None,
        sap_code: Optional[str] = None,
        approved: Optional[bool] = None,
        credit: Optional[bool] = None,
        created_at: Optional[date] = None,
        start_date: Optional[date] = None,
        finish_date: Optional[date] = None,
        payment_date: Optional[date] = None,
        status: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Заявки": ["read"]}))
):
    filters = {k: v for k, v in locals().items() if v is not None and k not in ["db", "current_user"]}

    if client is not None:
        query = await ClientDAO.get_all(session=db, filters={"fullname": client})
        clients = db.execute(query).scalars().all()
        filters["client_id"] = [client.id for client in clients]

    if filters.get("department_id", None) is None:
        user = await UserDAO.get_by_attributes(session=db, filters={"id": current_user["id"]}, first=True)
        role_department_relations = user.role.roles_departments
        role_departments = [relation.department_id for relation in role_department_relations]
        filters["department_id"] = role_departments

    if current_user.get("clients", None):
        filters["client_id"] = current_user.get("clients")

    # role_expense_types = await RoleExpenseTypeDAO.get_by_attributes(session=db, filters={"role_id": current_user.get("role_id")})
    # if role_expense_types:
    #     expense_type_ids = [expense_type.expense_type_id for expense_type in role_expense_types]
    #     filters["expense_type_id"] = expense_type_ids


    query = await RequestDAO.get_all(
        session=db,
        filters=filters if filters else None
    )

    if start_date is not None and finish_date is not None:
        # query = query.filter(func.date(RequestDAO.model.created_at).between(start_date, finish_date))
        query = query.filter(func.date(RequestDAO.model.payment_time).between(start_date, finish_date))

    result = db.execute(query.order_by(RequestDAO.model.number.desc())).scalars().all()
    return paginate(result)



@requests_router.get("/requests/{id}", response_model=Request)
async def get_request(
        id: UUID,
        start_date: Optional[date] = None,
        finish_date: Optional[date] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Заявки": ["read", "accounting", "transfer", "purchase requests"]}))
):
    obj = await RequestDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    if obj.exchange_rate is not None:
        obj.currency_sum = obj.sum / obj.exchange_rate
    else:
        obj.currency_sum = obj.sum

    if obj.payment_time is not None:
        payment_date = obj.payment_time.date()
        department_id = obj.department_id
        expense_type_id = obj.expense_type_id
        request_sum = obj.sum
        budget = (await BudgetDAO.get_filtered_budget_sum(
            session=db,
            department_id=department_id,
            expense_type_id=expense_type_id,
            start_date=payment_date,
            finish_date=payment_date
        ))[0]
        budget = budget if budget is not None else 0
        expense = (await BudgetDAO.get_filtered_budget_expense(
            session=db,
            department_id=department_id,
            expense_type_id=expense_type_id,
            start_date=payment_date,
            finish_date=payment_date
        ))[0]
        expense = -expense if expense is not None else 0
        obj.expense_type_budget = budget - expense - request_sum

        department_budget = (
            await DepartmentDAO.get_department_total_budget(
                session=db,
                department_id=department_id,
                start_date=None,
                finish_date=None,
                payment_date=payment_date
            )
        )[0]
        department_budget = department_budget if department_budget is not None else 0
        department_expense = (
            await DepartmentDAO.get_department_expense(
                session=db,
                department_id=department_id,
                start_date=None,
                finish_date=None,
                payment_date=payment_date
            )
        )[0]
        department_expense = -department_expense if department_expense is not None else 0
        obj.department_budget = department_budget - department_expense - request_sum

    return obj



@requests_router.put("/requests", response_model=Request)
async def update_request(
        body: UpdateRequest,
        db: Session = Depends(get_db),
        current_user: dict = Depends(
            PermissionChecker(
                required_permissions={
                    "Заявки": ["update", "accounting 2", "edit_purchase_request", "check"]
                }
            )
        )
):
    body_dict = body.model_dump(exclude_unset=True)
    body_dict.pop("file_paths", None)
    body_dict.pop("invoice", None)
    body_dict.pop("contract", None)
    body_dict.pop("client_id", None)
    request = await RequestDAO.get_by_attributes(session=db, filters={"id": body.id}, first=True)
    request_payment_time = request.payment_time.date()

    if request.status == 5:
        raise HTTPException(status_code=404, detail="Данная завка уже закрыта !")

    if body.payment_time is not None and body.status is None:
        if request_payment_time is not None and (request.status == 2 or request.status == 3):
            body_dict["status"] = 1


    if body.status == 4:
        if "reject" not in current_user["permissions"]["Заявки"]:
            body_dict.pop("status", None)
            body_dict.pop("comment", None)
            raise HTTPException(status_code=404, detail="У вас нет прав отменить статус заявки !")

    if body.approved is True:
        if "approve" not in current_user["permissions"]["Заявки"]:
            body_dict.pop("approved", None)
            body_dict.pop("approve_comment", None)
            raise HTTPException(status_code=404, detail="У вас нет прав одобрить заявку !")

        if body.status == 6 and body.payment_time is not None:
            request_payment_time = body.payment_time

        if request_payment_time is not None:
            if not request.credit:
                budget = (await BudgetDAO.get_filtered_budget_sum(
                    session=db,
                    department_id=request.department_id,
                    expense_type_id=request.expense_type_id,
                    start_date=request_payment_time,
                    finish_date=request_payment_time
                ))[0]
                budget = budget if budget is not None else 0
                expense = (await BudgetDAO.get_filtered_budget_expense(
                    session=db,
                    department_id=request.department_id,
                    expense_type_id=request.expense_type_id,
                    start_date=request_payment_time,
                    finish_date=request_payment_time
                ))[0]
                expense = -expense if expense is not None else 0
                balance = budget - expense
                if request.sum > balance:
                    raise HTTPException(status_code=400, detail="Недостаточно средств в бюджете !")


    if body.purchase_approved is True:
        if "approve purchase" not in current_user["permissions"]["Заявки"]:
            body_dict.pop("purchase_approved", None)
            raise HTTPException(status_code=404, detail="У вас нет прав одобрить заявку для закупа !")

    if body.checked_by_financier is True:
        if "check" not in current_user["permissions"]["Заявки"]:
            body_dict.pop("checked_by_financier", None)
            raise HTTPException(status_code=404, detail="У вас нет прав проверить заявку как финансист !")

    if body.credit is True:
        if "credit" not in current_user["permissions"]["Заявки"]:
            body_dict.pop("credit", None)
            raise HTTPException(status_code=404, detail="У вас нет прав включить заявку в долг !")

    if body.payment_type_id is not None:
        if request.payment_type_id != body.payment_type_id:
            if "change_payment_type" not in current_user["permissions"]["Заявки"]:
                body_dict.pop("payment_type_id", None)
                raise HTTPException(status_code=404, detail="У вас нет прав изменить тип оплаты заявки !")


    if body.to_accounting is True:
        if request.payment_type_id != UUID("88a747c1-5616-437c-ac71-a02b30287ee8"):
            body_dict.pop("to_accounting", None)
            raise HTTPException(status_code=404, detail="Тип оплаты не является перечислением !")

    if body.to_transfer is True:
        if request.payment_type_id != UUID("eda54dd2-2eef-430e-ae4e-0c4d68a44298"):
            body_dict.pop("to_transfer", None)
            raise HTTPException(status_code=404, detail="Тип оплаты не является переводом !")

    if body.status == 5:
        if request.payment_type_id == UUID("88a747c1-5616-437c-ac71-a02b30287ee8"):
            if request.to_accounting is False:
                body_dict.pop("status", None)
                raise HTTPException(status_code=404, detail="Сначала отправьте в бухгалтерию !")
            if request.invoice is None:
                body_dict.pop("status", None)
                raise HTTPException(status_code=404, detail="Сначала загрузите квитанцию оплаты !")

        if request.payment_type_id == UUID("eda54dd2-2eef-430e-ae4e-0c4d68a44298"):
            if request.to_transfer is False:
                body_dict.pop("status", None)
                raise HTTPException(status_code=404, detail="Сначала отправьте в переводы !")
            if request.invoice is None:
                body_dict.pop("status", None)
                raise HTTPException(status_code=404, detail="Сначала загрузите квитанцию оплаты !")

    if body.sum is not None or body.currency is not None:
        request_currency = request.currency
        new_currency = body.currency
        if request_currency != "Сум" or new_currency != "Сум":
            currency_response = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/")
            if currency_response.status_code == 200:
                ccy = ""
                if body.sum is not None and body.currency is None:
                    if request_currency == "Доллар":
                        ccy = "USD"
                    elif request_currency == "Евро":
                        ccy = "EUR"
                    elif request_currency == "Тенге":
                        ccy = "KZT"
                    elif request_currency == "Фунт":
                        ccy = "GBP"
                    elif request_currency == "Рубль":
                        ccy = "RUB"

                else:
                    if new_currency == "Доллар":
                        ccy = "USD"
                    elif new_currency == "Евро":
                        ccy = "EUR"
                    elif new_currency == "Тенге":
                        ccy = "KZT"
                    elif new_currency == "Фунт":
                        ccy = "GBP"
                    elif new_currency == "Рубль":
                        ccy = "RUB"

                cbu_currencies = currency_response.json()
                currency_dict = next((item for item in cbu_currencies if item["Ccy"] == ccy), None)
                exchange_rate = float(currency_dict["Rate"])

            else:
                raise HTTPException(
                    status_code=404,
                    detail="Что-то пошло не так, выберите заново валюту!"
                )

            sum = float(body.sum) * exchange_rate
            body_dict["sum"] = sum
            body_dict["exchange_rate"] = exchange_rate
        else:
            body_dict["sum"] = body.sum

        insert_data = {
            "sum": body.sum,
            "currency": body.currency,
            "request_id": body.id,
            "user_id": current_user["id"]
        }

        # create logs
        await LogDAO.add(
            session=db,
            **insert_data
        )
        db.commit()

    updated_request = await RequestDAO.update(session=db, data=body_dict)

    transaction = await TransactionDAO.get_by_attributes(session=db, filters={"request_id": updated_request.id}, first=True)
    if transaction:
        data = {
            "id": transaction.id,
            "status": updated_request.status
        }
        if body_dict.get("sum"):
            data["value"] = body_dict.get("sum")

        await TransactionDAO.update(session=db, data=data)

    db.commit()
    db.refresh(updated_request)

    if body.file_paths is not None and body.contract is not None:
        contract = await ContractDAO.add(session=db, **{"request_id": updated_request.id})
        await FileDAO.add(
            session=db,
            **{
                "file_paths": body.file_paths,
                "contract_id": contract.id if contract is not None else None
            }
        )

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

    if body.purchase_approved is True:
        insert_data = {
            "request_id": updated_request.id,
            "purchase_approved": updated_request.purchase_approved,
        }
        if body.client_id is not None:
            insert_data["client_id"] = body.client_id
        else:
            insert_data["user_id"] = current_user["id"]

        await LogDAO.add(
            session=db,
            **insert_data
        )
        db.commit()
        db.refresh(updated_request)

    if body.approved is True:
        insert_data = {
            "request_id": updated_request.id,
            "approved": updated_request.approved,
        }
        if body.client_id is not None:
            insert_data["client_id"] = body.client_id
        else:
            insert_data["user_id"] = current_user["id"]

        await LogDAO.add(
            session=db,
            **insert_data
        )
        db.commit()
        db.refresh(updated_request)

        chat_id = updated_request.client.tg_id if updated_request.client else None
        number = updated_request.number
        message_text = f"Ваша заявка #{number}s одобрена !"
        try:
            send_telegram_message(chat_id=chat_id, message_text=message_text)
        except Exception as e:
            print("Sending Error: ", e)

    if body.status is not None:
        insert_data = {
            "status": body.status,
            "request_id": updated_request.id
        }
        if body.client_id is not None:
            insert_data["client_id"] = body.client_id
        else:
            insert_data["user_id"] = current_user["id"]

        # create logs
        await LogDAO.add(
            session=db,
            **insert_data
        )
        db.commit()
        db.refresh(updated_request)

    message_text = ""
    chat_id = updated_request.client.tg_id if updated_request.client is not None else None
    inline_keyboard = None

    request_sum = format(int(request.sum), ',').replace(',', ' ')
    if request.exchange_rate is not None:
        requested_currency = '{:,.2f}'.format((request.sum / request.exchange_rate), ',').replace(',', ' ')
    else:
        requested_currency = request_sum

    request_text = (
        f"📌 Заявка #{request.number}s\n\n"
        f"📅 Дата заявки: {request.created_at.strftime('%d.%m.%Y')}\n"
        f"📍 Отдел: {request.department.name}\n"
        f"👤 Заявитель: {request.client.fullname if request.client else request.user.fullname}\n"
        f"📞 Номер заявителя: {request.client.phone if request.client else request.user.phone}\n"
        f"🛒 Заказчик: {request.buyer}\n"
        f"💰 Тип затраты: {request.expense_type.name}\n"
        f"🏢 Поставщик: {request.supplier}\n\n"
        f"💲 Стоимость: {request_sum}\n"
        f"💲 Запрошенная сумма в валюте: {requested_currency}\n"
        f"💵 Валюта: {request.currency if request.currency else ''}\n"
        f"📈 Курс валюты: {request.exchange_rate if request.exchange_rate else ''}\n"
        f"💳 Тип оплаты: {request.payment_type.name}\n"
        f"💳 Карта перевода: {request.payment_card if request.payment_card is not None else ''}\n"
        f"📜 № Заявки в SAP: {request.sap_code}\n"
        f"🕓 Дата оплаты: {request.payment_time}\n"
        f"💸 Фирма-плательщик: {request.payer_company.name if request.payer_company is not None else ''}\n\n"
        f"📝 Комментарии: {request.description}\n\n"
        + (f"📃 Документы оплаты 👇\n" if request.invoice else "")
    )

    status = updated_request.status
    number = updated_request.number
    if status == 1: # Принят
        message_text = (f"Ваша заявка #{number}s принята со стороны  финансового отдела.\n"
                        f"Срок оплаты {updated_request.payment_time.strftime('%d.%m.%Y')}")
        try:
            send_telegram_message(chat_id=chat_id, message_text=message_text, keyboard=inline_keyboard)
        except Exception as e:
            error_sender(error_message=f"FINANCE BACKEND: \n{e}")

        if request.payment_type_id == UUID("822e49f7-f54e-481e-997d-e4cb81b061e1"): # cash
            chat_id = settings.CHAT_GROUP  # chat id of group
            try:
                send_telegram_message(chat_id=chat_id, message_text=request_text, keyboard=inline_keyboard)
            except Exception as e:
                error_sender(error_message=f"FINANCE BACKEND: \n{e}")

    elif status == 4: # Отменен
        message_text = (f"Ваша заявка #{number}s отменена по причине:\n"
                        f"{updated_request.comment}")
        send_telegram_message(chat_id=chat_id, message_text=message_text, keyboard=inline_keyboard)

    elif status == 5: # Обработан
        try:
            send_telegram_message(chat_id=chat_id, message_text=f"Оплачено✅\n\n{request_text}", keyboard=inline_keyboard)
            if updated_request.invoice is not None:
                files = updated_request.invoice.file
                for file in files:
                    file_paths = file.file_paths
                    for file_path in file_paths:
                        send_telegram_document(chat_id=chat_id, file_path=file_path)
        except Exception as e:
            print("Sending Error: ", e)

    if body.payment_time is not None and request_payment_time is not None:
        message_text = (f"Срок оплаты по вашей заявке {updated_request.number} изменен с "
                        f"{request_payment_time.strftime('%d.%m.%Y')} на "
                        f"{updated_request.payment_time.strftime('%d.%m.%Y')} по причине:\n"
                        f"“{updated_request.comment}”")
        try:
            send_telegram_message(chat_id=chat_id, message_text=message_text)
        except Exception as e:
            print("Sending Error: ", e)

    return updated_request



@requests_router.post("/requests/excel")
async def get_excel_file(
        body : GenerateExcel,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Заявки": ["read"]}))
):
    body.finish_date += timedelta(days=1)
    body_dict = body.model_dump(exclude_unset=True)
    filters = {k: v for k, v in body_dict.items() if v is not None}
    if "client" in body_dict:
        query = await ClientDAO.get_all(session=db, filters={"fullname": body.client})
        clients = db.execute(query).scalars().all()
        filters.pop("client", None)
        filters["client_id"] = [client.id for client in clients]

    query = await RequestDAO.get_excel(session=db, filters=filters)
    file_name = excel_generator(data=query)
    return {'file_name': file_name}

