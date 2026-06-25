from sqlalchemy.orm import Session
from domain.user.user_schema import UserCreate
from models import Users
from passlib.context import CryptContext
from dotenv import load_dotenv
import os

load_dotenv()

passwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_ACCOUNT = int(os.getenv("MAX_ACCOUNT"))

def get_existing_user(db: Session, user_create: UserCreate):
    return db.query(Users).filter(Users.name == user_create.name).first()

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
    db.commit()
    return True
