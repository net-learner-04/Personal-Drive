from sqlalchemy.orm import Session
from domain.user.user_schema import UserCreate
from models import Users
from passlib.context import CryptContext


passwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MAX_ACCOUNT = 4


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


def get_user(db: Session, username: str):
    return db.query(Users).filter(Users.name == username).first()


def get_existing_user(db: Session, user_create: UserCreate):
    return db.query(Users).filter(Users.name == user_create.name).first()
