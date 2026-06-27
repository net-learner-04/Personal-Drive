from sqlalchemy.orm import Session
from domain.user.user_schema import UserCreate
from models import Users
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
import shutil

load_dotenv()

passwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_ACCOUNT = int(os.getenv("MAX_ACCOUNT"))


def get_existing_user(db: Session, user_create: UserCreate):
    return db.query(Users).filter(Users.name == user_create.name).first()


def get_user(db: Session, username: str):
    return db.query(Users).filter(Users.name == username).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(Users).filter(Users.id == user_id).first()


def create_user(db: Session, user_create: UserCreate):
    user_count = db.query(Users).count()
    if user_count >= MAX_ACCOUNT:
        return False

    db_user = Users(
        name=user_create.name,
        passwd=passwd_context.hash(user_create.passwd1),
        email=user_create.email
    )
    db.add(db_user)
    db.flush()

    from datetime import datetime
    date_str = datetime.now().strftime("%Y%m%d")
    dir_name = f"{db_user.id}_{db_user.name}_{date_str}"
    storage_path = os.path.join("uploads", dir_name)
    os.makedirs(storage_path, exist_ok=True)

    db_user.storage_path = storage_path
    db.commit()
    return True


def verify_password(db: Session, user: Users, password: str):
    return passwd_context.verify(password, user.passwd)


def update_name(db: Session, user: Users, new_name: str):
    user.name = new_name
    db.commit()


def update_email(db: Session, user: Users, new_email: str):
    user.email = new_email
    db.commit()


def delete_user(db: Session, user: Users):
    if user.storage_path and os.path.exists(user.storage_path):
        shutil.rmtree(user.storage_path)
    db.delete(user)
    db.commit()
