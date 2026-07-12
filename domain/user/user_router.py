from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm

from db import get_db
from models import Users
from auth import create_access_token, get_current_user
from mailer import send_reset_code, send_register_code, verify_code
from domain.user import user_crud, user_schema
from domain.user.user_crud import passwd_context


router = APIRouter(prefix="/api/user")


def require_admin(current_user: Users = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return current_user


@router.post("/email/verify-request")
def email_verify_request(body: user_schema.EmailVerifyRequest, db: Session = Depends(get_db)):
    existing = db.query(Users).filter(Users.email == body.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use.")
    send_register_code(body.email)
    return {"message": "Verification code sent."}


@router.post("/email/verify-confirm")
def email_verify_confirm(body: user_schema.EmailVerifyConfirm):
    if not verify_code(body.email, body.code, code_type="register"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code.")
    return {"message": "Email verified."}


@router.post("/create", status_code=status.HTTP_204_NO_CONTENT)
def user_create(_user_create: user_schema.UserCreate, db: Session = Depends(get_db)):
    user = user_crud.get_existing_user(db, user_create=_user_create)
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This user already exists.")
    result = user_crud.create_user(db=db, user_create=_user_create)
    if not result:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Maximum number of members ({user_crud.MAX_ACCOUNT}) has been exceeded.")


@router.post("/login", response_model=user_schema.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user, error = user_crud.check_login(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)
    access_token = create_access_token(data={"sub": user.name})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/settings/verify")
def verify_password_for_settings(
    body: user_schema.UserVerifyPassword,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user_crud.verify_password(db, current_user, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password.")
    return {"message": "Password verified."}


@router.patch("/settings/name")
def update_name(
    body: user_schema.UserUpdateName,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user_crud.verify_password(db, current_user, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password.")
    existing = db.query(Users).filter(Users.name == body.new_name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken.")
    user_crud.update_name(db, current_user, body.new_name)
    new_token = create_access_token(data={"sub": body.new_name})
    return {"message": "Username updated.", "access_token": new_token}


@router.patch("/settings/email")
def update_email(
    body: user_schema.UserUpdateEmail,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user_crud.verify_password(db, current_user, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password.")
    existing = db.query(Users).filter(Users.email == body.new_email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use.")
    user_crud.update_email(db, current_user, body.new_email)
    return {"message": "Email updated."}


@router.patch("/settings/password")
def update_password(
    body: user_schema.UserUpdatePassword,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user_crud.verify_password(db, current_user, body.current_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect.")
    user_crud.update_password(db, current_user, body.new_password)
    return {"message": "Password updated."}


@router.get("/me", response_model=user_schema.UserResponse)
def get_me(current_user: Users = Depends(get_current_user)):
    return current_user


@router.delete("/settings/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    body: user_schema.UserDelete,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin account cannot be deleted this way.")
    if not user_crud.verify_password(db, current_user, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password.")
    user_crud.delete_user(db, current_user)


@router.post("/password/reset-request")
def reset_request(email: str, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This email address does not exist.")
    send_reset_code(email)
    return {"message": "A verification code has been sent."}


@router.post("/password/reset")
def reset_password(email: str, code: str, new_password: str, db: Session = Depends(get_db)):
    if not verify_code(email, code, code_type="reset"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The verification code is incorrect or has expired.")
    user = db.query(Users).filter(Users.email == email).first()
    user_crud.update_password(db, user, new_password)
    return {"message": "Your password has been changed."}


@router.get("/admin/users", response_model=list[user_schema.UserResponse])
def admin_get_users(
    db: Session = Depends(get_db),
    current_user: Users = Depends(require_admin)
):
    return user_crud.get_all_users(db)


@router.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(require_admin)
):
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete admin account.")
    user_crud.delete_user(db, user)


@router.patch("/admin/users/{user_id}/unlock", status_code=status.HTTP_204_NO_CONTENT)
def admin_unlock_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(require_admin)
):
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user_crud.unlock_user(db, user)
