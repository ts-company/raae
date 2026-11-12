from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SECRET_KEY = os.getenv("EMAIL_VERIFICATION_SECRET")
serializer = URLSafeTimedSerializer(SECRET_KEY)

APP_BASE_URL = os.getenv("APP_BASE_URL")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")
PASSWORD_RESET_SALT = os.getenv("PASSWORD_RESET_SALT")


def send_verification_email(user_id: int, email: str) -> None:
    token = serializer.dumps({"user_id": user_id, "email": email}, salt="email-verify")
    verify_url = f"{APP_BASE_URL}/verify-email/{token}"

    msg = MIMEMultipart()
    msg["Subject"] = "Verify your email"
    msg["From"] = FROM_EMAIL
    msg["To"] = email

    body = f"""
    Hi,

    Please verify your email by clicking the link below:

    {verify_url}

    This link expires in 10 minutes.

    If you didn't request this, you can ignore this email.
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except smtplib.SMTPException as e:
        raise RuntimeError(f"Failed to send verification email: {e}")

def send_password_reset_email(user_id: int, email: str) -> None:
    token = serializer.dumps({"user_id": user_id, "email": email}, salt=PASSWORD_RESET_SALT)
    reset_url = f"{APP_BASE_URL}/reset-password/{token}"

    msg = MIMEMultipart()
    msg["Subject"] = "Reset your password"
    msg["From"] = FROM_EMAIL
    msg["To"] = email

    body = f"""
    Hi,

    We received a request to reset your password. Click the link below to choose a new one:

    {reset_url}

    This link expires in 10 minutes.

    If you didn't request this, you can safely ignore this email.
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_USER:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except smtplib.SMTPException as e:
        raise RuntimeError(f"Failed to send verification email: {e}")