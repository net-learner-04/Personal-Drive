import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"


verify_store = {}


def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))


def send_reset_code(to: str):
    code = generate_code()
    expire = datetime.now() + timedelta(minutes=5)
    verify_store[to] = {"code": code, "expire": expire}

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to
    msg['Subject'] = "Password Reset Verification Code."
    body = f"<h3>Verification Code: <b>{code}</b></h3><p>Please enter this within 5 minutes.</p>"
    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def verify_code(email: str, code: str) -> bool:
    entry = verify_store.get(email)
    if not entry:
        return False
    if datetime.now() > entry["expire"]:
        del verify_store[email]
        return False
    if entry["code"] != code:
        return False
    del verify_store[email]
    return True
