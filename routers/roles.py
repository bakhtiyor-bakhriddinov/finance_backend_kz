from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.session import get_db
from dal.dao import RoleDAO, AccessDAO, RoleDepartmentDAO, DepartmentDAO
from schemas.roles import GetRole, CreateRole, GetRoles, UpdateRole
from utils.utils import PermissionChecker

roles_router = APIRouter()



@roles_router.post("/roles", response_model=GetRole)
async def create_role(
        body: CreateRole,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Роли": ["create"]}))
):
    permissions = body.permissions
    departments = body.departments
    body_dict = body.model_dump()
    body_dict.pop("permissions", None)
    body_dict.pop("departments", None)
    created_role = await RoleDAO.add(session=db, **body_dict)
    if permissions is not None:
        for permission in permissions:
            data = {"permission_id": permission, "role_id": created_role.id}
            await AccessDAO.add(session=db, **data)

        db.commit()
        db.refresh(created_role)
        role_accesses = created_role.accesses
        created_role.permissions = [access.permission for access in role_accesses]

    if departments is not None:
        for department in departments:
            data = {"department_id": department, "role_id": created_role.id}
            await RoleDepartmentDAO.add(session=db, **data)

        db.commit()
        db.refresh(created_role)

        role_department_relations = await RoleDepartmentDAO.get_by_attributes(session=db,
                                                                              filters={"role_id": created_role.id})
        created_role.departments = [relation.department for relation in role_department_relations]

    return created_role



@roles_router.get("/roles/{id}", response_model=GetRole)
async def get_role(
        id: UUID,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Роли": ["read"]}))
):
    role = await RoleDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    role.permissions = [access.permission for access in role.accesses]

    role_department_relations = await RoleDepartmentDAO.get_by_attributes(session=db,
                                                                          filters={"role_id": role.id})
    role.departments = [relation.department for relation in role_department_relations]
    # role_departments = [relation.department_id for relation in role_department_relations]

    # departments = await DepartmentDAO.get_by_attributes(session=db)
    # departments = [department for department in departments if
    #                department.id in role_departments] if role_departments else [department for department in
    #                                                                             departments]
    # role.departments = departments

    return role


@roles_router.get("/roles", response_model=List[GetRoles])
async def get_role_list(
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Роли": ["read"]}))
):
    roles = await RoleDAO.get_by_attributes(session=db)
    return roles



@roles_router.put("/roles", response_model=GetRole)
async def update_role(
        body: UpdateRole,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Роли": ["update"]}))
):
    permissions = body.permissions
    departments = body.departments
    body_dict = body.model_dump(exclude_unset=True)
    body_dict.pop("permissions", None)
    body_dict.pop("departments", None)
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

        db.commit()
        db.refresh(updated_role)
        role_accesses = updated_role.accesses
        updated_role.permissions = [access.permission for access in role_accesses]

    if departments is not None:
        role_department_relations = updated_role.roles_departments
        role_departments = [relation.department_id for relation in role_department_relations]

        for department in role_departments:
            if department not in departments:
                await RoleDepartmentDAO.delete(session=db, filters={"department_id": department, "role_id": updated_role.id})

        for department in departments:
            if department not in role_departments:
                data = {"department_id": department, "role_id": updated_role.id}
                await RoleDepartmentDAO.add(session=db, **data)

        db.commit()
        db.refresh(updated_role)

    role_department_relations = await RoleDepartmentDAO.get_by_attributes(session=db,
                                                                          filters={"role_id": updated_role.id})
    updated_role.departments = [relation.department for relation in role_department_relations]

    return updated_role


# @roles_router.delete("/roles", response_model=List[GetRoles])
# async def delete_role(
#         id: Optional[UUID],
#         db: Session = Depends(get_db),
#         current_user: dict = Depends(PermissionChecker(required_permissions={"Roles": ["delete"]}))
# ):
#     deleted_roles = await RoleDAO.delete(session=db, filters={"id": id})
#     # deleted_role.permissions = [access.permission for access in deleted_role.accesses]
#     db.commit()
#     return deleted_roles

