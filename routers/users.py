from datetime import timedelta, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_pagination import Page, paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.config import settings
from core.session import get_db
from dal.dao import UserDAO
from schemas.users import CreateUser, GetUser, GetUsers, UpdateUser
from utils.utils import Hasher, create_access_token, PermissionChecker, get_me

users_router = APIRouter()



@users_router.post('/login')
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: Session= Depends(get_db)
):
    user = await UserDAO.get_by_attributes(session=session, filters={"username": form_data.username}, first=True)
    if not user or not Hasher.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=404, detail="Invalid username or password")

    permissions = {}
    if user.role.accesses:
        for access in user.role.accesses:
            # permissions.append(access.permission.name)
            try:
                permissions[access.permission.group.name].append(access.permission.name)
            except KeyError:
                permissions[access.permission.group.name] = [access.permission.name]

    user_info = {
        "id": str(user.id),
        "fullname": user.fullname,
        "username": user.username,
        "password": user.password,
        "permissions": permissions
    }
    expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    if user.username == settings.BOT_USER:
        data = {
            "sub": user.username,
            "user": user_info
        }
    else:
        data = {
            "sub": user.username,
            "exp": expire,
            "user": user_info
        }

    return {
        "access_token": create_access_token(data=data),
        "token_type": "Bearer"
    }


@users_router.get('/me', response_model=GetUser)
async def get_me(
        current_user: GetUser = Depends(get_me)
):
    current_user.role.permissions = [access.permission for access in current_user.role.accesses]
    current_user.role.departments = [relation.department for relation in current_user.role.roles_departments]
    return current_user



# @user_router.get('/logout', status_code=status.HTTP_200_OK)
# async def logout(request: Request):
#     request.session.pop('user', None)
#     return RedirectResponse(url='/')


@users_router.post("/users", response_model=GetUser)
async def create_user(
        body: CreateUser,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Пользователи": ["create"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    body_dict["password"] = Hasher.get_password_hash(body.password)
    created_user = await UserDAO.add(session=db, **body_dict)
    db.commit()
    db.refresh(created_user)
    created_user.role.permissions = [access.permission for access in created_user.role.accesses]
    return created_user


@users_router.get("/users", response_model=Page[GetUsers])
async def get_user_list(
        is_active: Optional[bool] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Пользователи": ["read"]}))
):
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active

    users = await UserDAO.get_by_attributes(session=db, filters=filters if filters else None)
    return paginate(users)


@users_router.get("/users/{id}", response_model=GetUser)
async def get_user(
        id: UUID,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Пользователи": ["read"]}))
):
    user = await UserDAO.get_by_attributes(session=db, filters={"id": id}, first=True)
    user.role.permissions = [access.permission for access in user.role.accesses]
    return user


@users_router.put("/users", response_model=GetUser)
async def update_user(
        body: UpdateUser,
        db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Пользователи": ["update"]}))
):
    body_dict = body.model_dump(exclude_unset=True)
    body_dict["password"] = Hasher.get_password_hash(body.password)
    updated_user = await UserDAO.update(session=db, data=body_dict)
    db.commit()
    db.refresh(updated_user)
    return updated_user
