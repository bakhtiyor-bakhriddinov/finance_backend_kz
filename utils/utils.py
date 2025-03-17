import json
from datetime import datetime, timedelta
from typing import Optional

import requests
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette import status
import os
from passlib.context import CryptContext
from core.config import settings
from core.session import get_db
from dal.dao import UserDAO




# Token url (We should later create a token url that accepts just a user and a password to use it with Swagger)
reuseable_oauth = OAuth2PasswordBearer(tokenUrl="/login", scheme_name="JWT")


# Error
CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Could not validate credentials',
    headers={'WWW-Authenticate': 'Bearer'},
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Hasher:
    @staticmethod
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password):
        return pwd_context.hash(password)



def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt




# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()



async def get_current_user(token: str = Depends(reuseable_oauth), session: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get('sub')
        expire_datetime = payload.get('exp')
        user = payload.get('user')
        print("username: ", username)
        print('last ',token)
        if username == settings.BOT_USER:
            print("user is entering",settings.BOT_USER)
            return user
        if datetime.fromtimestamp(expire_datetime) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Token is expired',
                headers={'WWW-Authenticate': 'Bearer'},
            )

    except Exception as e:
        print("this is the error",e)
        raise CREDENTIALS_EXCEPTION

    # user = await _get_user_by_username(session=session, username=username)
    # user = await _get_user_by_attributes(session=session, data={"username": username})
    if user is None:
        raise CREDENTIALS_EXCEPTION

    return user



class PermissionChecker:

    def __init__(self, required_permissions: dict):
        self.required_permissions = required_permissions

    def __call__(self, user: dict = Depends(get_current_user)) -> dict:
        permissions = user['permissions']
        key, value = next(iter(self.required_permissions.items()))
        permissions = permissions.get(key)
        need_permissions = list(set(value) & set(permissions)) if permissions else None
        if not need_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to use this api",
            )
        return user



async def get_me(token: str = Depends(reuseable_oauth), session: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get('sub')
        expire_datetime = payload.get('exp')
        if datetime.fromtimestamp(expire_datetime) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Token is expired',
                headers={'WWW-Authenticate': 'Bearer'},
            )

    except (JWTError, ValidationError):
        raise CREDENTIALS_EXCEPTION

    user_obj = await UserDAO.get_by_attributes(session=session, filters={"username": username}, first=True)
    if user_obj is None:
        raise CREDENTIALS_EXCEPTION

    return user_obj


def send_telegram_message(chat_id, message_text, keyboard: Optional[dict] = None):
    # Create the request payload
    payload = {
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "HTML"
    }
    if keyboard:
        payload['reply_markup'] = json.dumps(keyboard)

    # Send the request to send the inline keyboard message
    response = requests.post(
        url=f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
        json=payload
    )
    # Check the response status
    if response.status_code == 200:
        return response
    else:
        return None

