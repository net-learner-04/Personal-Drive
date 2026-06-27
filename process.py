import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette import status
from db import get_db
from models import Users, Files
from dotenv import load_dotenv
from auth import get_current_user
from datetime import datetime


load_dotenv()

UPLOAD_DIR = str(os.getenv("UPLOAD_DIR"))

os.makedirs(UPLOAD_DIR, exist_ok=True)


router = APIRouter(prefix="/api/file")


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    file_path = os.path.join(current_user.storage_path, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    db_file = Files(
        file_name=file.filename,
        file_path=file_path,
        file_size=file_size,
        file_owner=current_user.id,
        file_type=file.content_type,
        is_deleted=False,
        create_date=datetime.now()
    )
    db.add(db_file)
    db.commit()

    return {"filename": file.filename, "size": file_size}


@router.get("/list")
def get_file_list(
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    files = db.query(Files).filter(
        Files.file_owner == current_user.id,
        Files.is_deleted == False
    ).all()
    return files


@router.get("/download/{file_id}")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    file = db.query(Files).filter(
        Files.id == file_id,
        Files.file_owner == current_user.id,
        Files.is_deleted == False
    ).first()

    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The file cannot be found.")

    return FileResponse(path=file.file_path, filename=file.file_name)


@router.delete("/delete/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    file = db.query(Files).filter(
        Files.id == file_id,
        Files.file_owner == current_user.id,
        Files.is_deleted == False
    ).first()

    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The file cannot be found.")

    file.is_deleted = True
    db.commit()
