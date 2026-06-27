from sqlalchemy.orm import Session
from domain.user.user_schema import UserCreate
from models import Users
from passlib.context import CryptContext
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import shutil

load_dotenv()

passwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_ACCOUNT = int(os.getenv("MAX_ACCOUNT"))
MAX_FAILED_LOGIN = 5
LOCKOUT_MINUTES = 15


def get_existing_user(db: Session, user_create: UserCreate):
    return db.query(Users).filter(Users.name == user_create.name).first()


def get_user(db: Session, username: str):
    return db.query(Users).filter(Users.name == username).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(Users).filter(Users.id == user_id).first()


def get_all_users(db: Session):
    return db.query(Users).all()


def create_user(db: Session, user_create: UserCreate, is_admin: bool = False):
    if not is_admin:
        user_count = db.query(Users).filter(Users.is_admin == False).count()
        if user_count >= MAX_ACCOUNT:
            return False

    db_user = Users(
        name=user_create.name,
        passwd=passwd_context.hash(user_create.passwd1),
        email=user_create.email,
        is_admin=is_admin
    )
    db.add(db_user)
    db.flush()

    date_str = datetime.now().strftime("%Y%m%d")
    dir_name = f"{db_user.id}_{db_user.name}_{date_str}"
    storage_path = os.path.join("uploads", dir_name)
    os.makedirs(storage_path, exist_ok=True)

    db_user.storage_path = storage_path
    db.commit()
    return True


def create_admin_if_not_exists(db: Session):
    admin_name = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_email = os.getenv("ADMIN_EMAIL")

    if not admin_name or not admin_password:
        return

    existing = db.query(Users).filter(Users.name == admin_name).first()
    if existing:
        return

    from domain.user.user_schema import UserCreate
    admin_create = UserCreate(
        name=admin_name,
        passwd1=admin_password,
        passwd2=admin_password,
        email=admin_email or f"{admin_name}@localhost"
    )
    create_user(db, admin_create, is_admin=True)


def verify_password(db: Session, user: Users, password: str):
    return passwd_context.verify(password, user.passwd)


def check_login(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return None, "User not found."

    if user.locked_until and datetime.now() < user.locked_until:
        remaining = int((user.locked_until - datetime.now()).total_seconds() / 60) + 1
        return None, f"Account locked. Try again in {remaining} minute(s)."

    if not passwd_context.verify(password, user.passwd):
        user.failed_login = (user.failed_login or 0) + 1
        if user.failed_login >= MAX_FAILED_LOGIN:
            user.locked_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
            user.failed_login = 0
            db.commit()
            return None, f"Too many failed attempts. Account locked for {LOCKOUT_MINUTES} minutes."
        db.commit()
        remaining_attempts = MAX_FAILED_LOGIN - user.failed_login
        return None, f"Incorrect password. {remaining_attempts} attempt(s) remaining."

    user.failed_login = 0
    user.locked_until = None
    db.commit()
    return user, None


def update_name(db: Session, user: Users, new_name: str):
    user.name = new_name
    db.commit()


def update_email(db: Session, user: Users, new_email: str):
    user.email = new_email
    db.commit()


def update_password(db: Session, user: Users, new_password: str):
    user.passwd = passwd_context.hash(new_password)
    db.commit()


def delete_user(db: Session, user: Users):
    if user.storage_path and os.path.exists(user.storage_path):
        shutil.rmtree(user.storage_path)
    db.delete(user)
    db.commit()


def unlock_user(db: Session, user: Users):
    user.failed_login = 0
    user.locked_until = None
    db.commit()
