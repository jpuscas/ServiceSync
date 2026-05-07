import os
import smtplib
from email.message import EmailMessage


def send_email(to_email, message):
    smtp_host = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", "587"))
    smtp_username = os.getenv("MAIL_USERNAME")
    smtp_password = os.getenv("MAIL_PASSWORD")
    default_sender = os.getenv("MAIL_DEFAULT_SENDER", smtp_username)
    subject = os.getenv("MAIL_SUBJECT", "ServiceSync Notification")

    if not smtp_username or not smtp_password:
        raise ValueError("Missing MAIL_USERNAME or MAIL_PASSWORD environment variables.")

    if not to_email:
        raise ValueError("Recipient email is required.")

    email = EmailMessage()
    email["Subject"] = subject
    email["From"] = default_sender
    email["To"] = to_email
    email.set_content(message)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(email)