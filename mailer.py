import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

verify_store = {}


def _generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))


def _send_email(to: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def send_reset_code(to: str):
    code = _generate_code()
    verify_store[to] = {"code": code, "expire": datetime.now() + timedelta(minutes=5), "type": "reset"}
    body = f"<h3>Password Reset Code: <b>{code}</b></h3><p>Valid for 5 minutes.</p>"
    _send_email(to, "[Personal-Drive] Password Reset Code", body)


def send_register_code(to: str):
    code = _generate_code()
    verify_store[to] = {"code": code, "expire": datetime.now() + timedelta(minutes=10), "type": "register"}
    body = f"<h3>Email Verification Code: <b>{code}</b></h3><p>Valid for 10 minutes.</p>"
    _send_email(to, "[Personal-Drive] Email Verification", body)


def verify_code(email: str, code: str, code_type: str = None):
    entry = verify_store.get(email)
    if not entry:
        return False
    if datetime.now() > entry["expire"]:
        del verify_store[email]
        return False
    if code_type and entry.get("type") != code_type:
        return False
    if entry["code"] != code:
        return False
    del verify_store[email]
    return True
