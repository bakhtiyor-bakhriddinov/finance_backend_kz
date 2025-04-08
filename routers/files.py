import os
from datetime import datetime
from typing import List, Union
from utils.utils import generate_random_string, error_sender

from fastapi import APIRouter, UploadFile
from fastapi import Depends, File

from utils.utils import PermissionChecker

from fastapi import FastAPI, Request, HTTPException, status
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import FileTarget, ValueTarget
from streaming_form_data.validators import MaxSizeValidator
import streaming_form_data
from starlette.requests import ClientDisconnect
from urllib.parse import unquote
import os

files_router = APIRouter()


@files_router.post("/files/upload")
async def upload_files(
        files: List[UploadFile] = File(...),
        # db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Файлы": ["create"]}))
):
    base_dir = "files"
    date_dir = datetime.now().strftime("%Y/%m/%d")  # Create a path like "2025/03/10"
    save_dir = os.path.join(base_dir, date_dir)

    os.makedirs(save_dir, exist_ok=True)  # Ensure the directory exists

    file_paths = []
    for file in files:
        file_path = os.path.join(save_dir, file.filename)
        with open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024)
                if not chunk:
                    break
                buffer.write(chunk)
        file_paths.append(file_path)

    return {"file_paths": file_paths}


@files_router.post("/files/upload/bot")
async def upload_bot_files(
        file: UploadFile = File(...),
        # db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Файлы": ["create"]}))
):
    base_dir = "files"
    date_dir = datetime.now().strftime("%Y/%m/%d")  # Create a path like "2025/03/10"
    save_dir = os.path.join(base_dir, date_dir)

    os.makedirs(save_dir, exist_ok=True)  # Ensure the directory exists

    file_paths = []
        

    file_path = os.path.join(save_dir, file.filename)
    with open(file_path, "wb") as buffer:
        while True:
            chunk = await file.read(1024)
            if not chunk:
                break
            buffer.write(chunk)
    file_paths.append(file_path)

    return {"file_paths": file_paths}


MAX_FILE_SIZE = 1024 * 1024 * 1024 * 4  # = 4GB
MAX_REQUEST_BODY_SIZE = MAX_FILE_SIZE + 1024


class MaxBodySizeException(Exception):
    def __init__(self, body_len: str):
        self.body_len = body_len

class MaxBodySizeValidator:
    def __init__(self, max_size: int):
        self.body_len = 0
        self.max_size = max_size

    def __call__(self, chunk: bytes):
        self.body_len += len(chunk)
        if self.body_len > self.max_size:
            raise MaxBodySizeException(body_len=self.body_len)


@files_router.post('/files/upload/bot/2')
async def upload(request: Request):
    body_validator = MaxBodySizeValidator(MAX_REQUEST_BODY_SIZE)
    filename = request.headers.get('filename')
    base_dir = "files"
    date_dir = datetime.now().strftime("%Y/%m/%d")  # Create a path like "2025/03/10"
    save_dir = os.path.join(base_dir, date_dir)
    os.makedirs(save_dir, exist_ok=True)  # Ensure the directory exists

    if not filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail='Filename header is missing')
    try:
        filename = unquote(filename)
        file_extension = os.path.splitext(filename)[1]

        filename = generate_random_string(10)+file_extension
        filepath = os.path.join(save_dir, os.path.basename(filename))
        file_ = FileTarget(filepath, validator=MaxSizeValidator(MAX_FILE_SIZE))
        data = ValueTarget()
        parser = StreamingFormDataParser(headers=request.headers)
        parser.register('file', file_)
        parser.register('data', data)

        async for chunk in request.stream():
            body_validator(chunk)
            parser.data_received(chunk)
    except ClientDisconnect:
        print("Client Disconnected")
    except MaxBodySizeException as e:
        error_sender(error_message=f"FINANCE BACKEND: \n{e}")
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f'Maximum request body size limit ({MAX_REQUEST_BODY_SIZE} bytes) exceeded ({e.body_len} bytes read)')
    except streaming_form_data.validators.ValidationError as e:
        error_sender(error_message=f"FINANCE BACKEND: \n{e}")
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f'Maximum file size limit ({MAX_FILE_SIZE} bytes) exceeded')
    except Exception as e:
        print("exception uploading file: ", e)
        error_sender(error_message=f"FINANCE BACKEND: \n{e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail='There was an error uploading the file')

    if not file_.multipart_filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='File is missing')


    return {"file_paths": [filepath]}
