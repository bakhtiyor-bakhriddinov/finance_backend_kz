import os
from datetime import datetime
from typing import List

from fastapi import APIRouter, UploadFile
from fastapi import Depends, File

from utils.utils import PermissionChecker

files_router = APIRouter()


@files_router.post("/files/upload")
async def upload_files(
        files: List[UploadFile] = File(...),
        # db: Session = Depends(get_db),
        current_user: dict = Depends(PermissionChecker(required_permissions={"Files": ["create"]}))
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
