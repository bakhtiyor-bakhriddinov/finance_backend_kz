from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from sqlalchemy.ext.asyncio import AsyncSession

from core.session import get_db
from dal.dao import RoleDAO, AccessDAO
from schemas.roles import GetRole, CreateRole, GetRoles, UpdateRole
from utils.utils import PermissionChecker

roles_router = APIRouter()



@roles_router.post("/roles", response_model=GetRole)
async def create_role(
        body: CreateRole,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Roles": ["create"]}))
):
    permissions = body.permissions
    body_dict = body.model_dump()
    body_dict.pop("permissions", None)
    created_role = await RoleDAO.add(session=db, **body_dict)
    if permissions is not None:
        for permission in permissions:
            data = {"permission_id": permission, "role_id": created_role.id}
            await AccessDAO.add(session=db, **data)

        await db.commit()
        await db.refresh(created_role)
        role_accesses = created_role.accesses
        created_role.permissions = [access.permission for access in role_accesses]

    return created_role



@roles_router.get("/roles/{id}", response_model=GetRole)
async def get_role(
        id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Roles": ["read"]}))
):
    role = await RoleDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    role.permissions = [access.permission for access in role.accesses]
    return role


@roles_router.get("/roles", response_model=List[GetRoles])
async def get_role_list(
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Roles": ["read"]}))
):
    roles = await RoleDAO.get_all(session=db)
    return roles



@roles_router.put("/roles", response_model=GetRole)
async def update_role(
        body: UpdateRole,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Roles": ["update"]}))
):
    permissions = body.permissions
    body_dict = body.model_dump(exclude_unset=True)
    body_dict.pop("permissions", None)
    updated_role = await RoleDAO.update(session=db, data=body_dict)
    if permissions is not None:
        role_accesses = updated_role.accesses
        role_permissions = [access.permission_id for access in role_accesses]

        for permission in role_permissions:
            if permission not in permissions:
                await AccessDAO.delete(session=db, filters={"permission_id": permission, "role_id": updated_role.id})

        for permission in permissions:
            if permission not in role_permissions:
                data = {"permission_id": permission, "role_id": updated_role.id}
                await AccessDAO.add(session=db, **data)

        await db.commit()
        await db.refresh(updated_role)
        role_accesses = updated_role.accesses
        updated_role.permissions = [access.permission for access in role_accesses]

    return updated_role


@roles_router.delete("/roles", response_model=List[GetRoles])
async def delete_role(
        id: Optional[UUID],
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Roles": ["delete"]}))
):
    deleted_roles = await RoleDAO.delete(session=db, filters={"id": id})
    # deleted_role.permissions = [access.permission for access in deleted_role.accesses]
    await db.commit()
    return deleted_roles

