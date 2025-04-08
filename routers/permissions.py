from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.session import get_db
from dal.dao import PermissionDAO, PermissionGroupDAO
from schemas.permissions import GetPermission, GetPermissionGroup
from utils.utils import PermissionChecker



permissions_router = APIRouter()



@permissions_router.get("/permission-groups", response_model=List[GetPermissionGroup])
async def get_permission_group_list(
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Разрешения": ["read"]}))
):
    permission_groups = await PermissionGroupDAO.get_by_attributes(session=db)
    return permission_groups



@permissions_router.get("/permissions", response_model=List[GetPermission])
async def get_permission_list(
        permission_group: Optional[UUID] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Разрешения": ["read"]}))
):
    filters = {}
    if permission_group is not None:
        filters["group_id"] = permission_group

    permissions = await PermissionDAO.get_by_attributes(session=db, filters=filters if filters else None)
    return permissions

