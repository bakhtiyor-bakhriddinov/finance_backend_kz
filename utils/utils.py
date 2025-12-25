import json
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import string
import random
import requests
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, HTTPBasicCredentials, HTTPBasic
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



security = HTTPBasic()

def get_current_user_for_docs(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = settings.docs_username
    correct_password = settings.docs_password
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username



async def get_current_user(token: str = Depends(reuseable_oauth), session: AsyncSession = Depends(get_db)):
    # print('current tokent',token)
    try:
        # print('before payload')
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # print('after payload')
        username = payload.get('sub')
        # print('after username')
        expire_datetime = payload.get('exp', None)
        # print('expire datetime')
        user = payload.get('user')
        # print("username: ", username)
        # if username == settings.BOT_USER:
        #     # print("user is entering",settings.BOT_USER)
        #     return user
        if expire_datetime is None:
            return user
        else:
            if datetime.fromtimestamp(expire_datetime) < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Token is expired',
                    headers={'WWW-Authenticate': 'Bearer'},
                )

    # except Exception as e:
    except (JWTError, ValidationError) as e:
        print("JWT ERROR: ", e)
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
        # permissions = user['permissions']
        # key, value = next(iter(self.required_permissions.items()))
        # permissions = permissions.get(key)
        # need_permissions = list(set(value) & set(permissions)) if permissions else None

        user_permissions = user['permissions']
        permission_group, required_permissions = next(iter(self.required_permissions.items()))
        user_permissions = user_permissions.get(permission_group, None)
        # need_permissions = set(required_permissions).issubset(user_permissions) if user_permissions else None
        need_permissions = set(required_permissions).intersection(user_permissions) if user_permissions else None
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
        print("Response text: ", response.text)
        return None


def send_telegram_document(chat_id, file_path):
    # Open the file in binary mode
    with open(file_path, "rb") as file:
        # Prepare data and files
        data = {
            "chat_id": chat_id
            # "caption": message_text  # Text message
        }
        files = {"document": file}  # Sending as a document

        # Send POST request
        response = requests.post(
            url=f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendDocument",
            data=data,
            files=files
        )
    # Check the response status
    if response.status_code == 200:
        return response
    else:
        print("Response text: ", response.text)
        return None




def generate_random_string(length=10):
    characters = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    return ''.join(random.choices(characters, k=length))



def error_sender(error_message):
    payload = {
        "chat_id": settings.ERROR_GROUP,
        "text": error_message,
        "parse_mode": "HTML"
    }

    # Send the request to send the inline keyboard message
    response = requests.post(
        url=f"https://api.telegram.org/bot{settings.ERROR_BOT}/sendMessage",
        json=payload
    )
    # Check the response status
    if response.status_code == 200:
        return response
    else:
        print("Response text: ", response.text)
        return None


status_data = {
    0: "Новый",
    1: "Принят",
    2: "Ожидает оплаты",
    3: "Просрочен",
    4: "Отклонен",
    5: "Обработан",
    6: "Отложен"
}
approved_data = {
    True: "Да",
    False: "Нет",
    None: "Не задано"
}

def excel_generator(data):
    columns = {
        "Номер заявки": [],
        "Код заявки SAP": [],
        "Дата запроса": [],
        "Отдел": [],
        "Одобрено": [],
        "Кредит": [],
        "Комментария": [],
        "Тип расхода": [],
        "Заказчик": [],
        "Закупщик": [],
        "Поставщик": [],
        "Сумма": [],
        "Валюта": [],
        "Курс валюты": [],
        "Запрошенная валюта": [],
        "Тип оплаты": [],
        "Дата оплаты": [],
        "Статус": []
    }
    for row in data:
        columns["Номер заявки"].append(row.number)
        columns["Номер приходной"].append(row.acceptance_number)
        columns["Дата запроса"].append(row.created_at.strftime("%d-%m-%Y"))
        columns["Отдел"].append(row.department.name)
        columns["Одобрено"].append(approved_data[row.approved])
        columns["Кредит"].append(approved_data[row.credit])
        columns["Комментария"].append(row.description)
        columns["Тип расхода"].append(row.expense_type.name)
        columns["Заказчик"].append(row.client.fullname)
        columns["Закупщик"].append(row.buyer)
        columns["Поставщик"].append(row.supplier)
        columns["Сумма"].append(row.sum)
        columns["Валюта"].append(row.currency)
        # print("Request number: ", row.number, "Sum: ", row.sum)
        if row.exchange_rate is not None:
            columns["Курс валюты"].append(row.exchange_rate)
            columns["Запрошенная валюта"].append(row.sum / row.exchange_rate)
        else:
            columns["Курс валюты"].append(" ")
            columns["Запрошенная валюта"].append(row.sum)
        columns["Тип оплаты"].append(row.payment_type.name)
        columns["Дата оплаты"].append(row.payment_time.strftime("%d-%m-%Y")) if row.payment_time else columns["Дата оплаты"].append(" ")
        columns['Статус'].append(status_data[row.status])

    file_name = f"files/Finance orders от {datetime.now().strftime('%d.%m.%Y')}.xlsx"
    df = pd.DataFrame(columns)
    # Generate Excel file
    df.to_excel(file_name, index=False)
    return file_name

