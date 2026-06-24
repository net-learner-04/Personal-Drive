from fastapi import APIRouter, HTTPException
from fastapi import Depends
from sqlalchemy.orm import Session
from starlette import status
from db import get_db
from domain.user import user_crud, user_schema
from fastapi.security import OAuth2PasswordRequestForm
from auth import create_access_token


router = APIRouter(
    prefix="/api/user"
)


@router.post("/create", status_code=status.HTTP_204_NO_CONTENT)
def user_create(_user_create: user_schema.UserCreate, db: Session=Depends(get_db)):
    user = user_crud.get_existing_user(db, user_create=_user_create)
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This user already exists.")
    user_crud.create_user(db=db, user_create=_user_create)


@router.post("/login", response_model=user_schema.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = user_crud.get_user(db, form_data.username)
    if not user or not passwd_context.verify(form_data.password, user.passwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your username or password is incorrect.",
        )
    access_token = create_access_token(data={"sub": user.name})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/password/reset-request")
def reset_request(email: str, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This email address does not exist.")
    send_reset_code(email)
    return {"message": "A verification code has been sent."}


@router.post("/password/reset")
def reset_password(email: str, code: str, new_password: str, db: Session = Depends(get_db)):
    if not verify_code(email, code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The verification code is incorrect or has expired.")
    user = db.query(Users).filter(Users.email == email).first()
    user.passwd = passwd_context.hash(new_password)
    db.commit()
    return {"message": "Your password has been changed."}