from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from sqlalchemy.ext.asyncio import AsyncSession

from core.session import get_db
from dal.dao import RequestDAO, InvoiceDAO, ContractDAO, FileDAO, LogDAO
from schemas.requests import Requests, Request, UpdateRequest, CreateRequest
from utils.utils import PermissionChecker



requests_router = APIRouter()




@requests_router.post("/requests", response_model=Request)
async def create_request(
        body: CreateRequest,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Requests": ["create"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    print("body_dict: ", body_dict)
    body_dict.pop("file_paths", None)
    body_dict.pop("contract", None)
    print("body_dict: ", body_dict)
    created_request = await RequestDAO.add(session=db, **body.model_dump())

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

    await db.commit()
    await db.refresh(created_request)
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
        status: Optional[int] = None,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Requests": ["read"]}))
):
    data = {
        "number": number,
        "client_id": client_id,
        "department_id": department_id,
        "expense_type_id": expense_type_id,
        "payment_type_id": payment_type_id,
        "sum": payment_sum,
        "sap_code": sap_code,
        "approved": approved,
        "created_at": created_at,
        "payment_time": payment_date,
        "status": status
    }
    filtered_data = {k: v for k, v in data.items() if v is not None}
    objs = await RequestDAO.get_all(
        session=db,
        filters=filtered_data
    )
    return paginate(objs)



@requests_router.get("/requests/{id}", response_model=Request)
async def get_request(
        id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Requests": ["read"]}))
):
    obj = await RequestDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    return obj



@requests_router.put("/requests", response_model=Request)
async def update_request(
        body: UpdateRequest,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Requests": ["update"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    body_dict.pop("file_paths", None)
    body_dict.pop("invoice", None)
    updated_request = await RequestDAO.update(session=db, data=body_dict)

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
    # create logs
    await LogDAO.add(
        session=db,
        **{
            "status": body.status,
            "request_id": updated_request.id,
            "user_id": current_user["id"]
        }
    )
    await db.commit()
    await db.refresh(updated_request)
    return updated_request
