import os
import re
import smtplib
from email.message import EmailMessage


CARRIER_SMS_DOMAINS = {
    "verizon": "vtext.com",
    "att": "txt.att.net",
    "at&t": "txt.att.net",
    "tmobile": "tmomail.net",
    "t-mobile": "tmomail.net",
    "sprint": "messaging.sprintpcs.com",
    "boost": "sms.myboostmobile.com",
    "cricket": "sms.cricketwireless.net",
    "xfinity": "vtext.com",  # sometimes differs; verify if needed
}


def normalize_phone_number(phone_number):
    if phone_number is None:
        return ''
    return re.sub(r'\D', '', str(phone_number))


def normalize_carrier(carrier):
    if carrier is None:
        return ''

    carrier_key = str(carrier).strip().lower()
    carrier_key = carrier_key.replace('&', 'and')
    carrier_key = carrier_key.replace('-', '')
    carrier_key = carrier_key.replace(' ', '')

    carrier_aliases = {
        'atandt': 'att',
        'att': 'att',
        'tmobile': 'tmobile',
        'tmobileus': 'tmobile',
        'verizonwireless': 'verizon',
        'boostmobile': 'boost',
        'cricketwireless': 'cricket',
        'xfinitymobile': 'xfinity',
    }

    return carrier_aliases.get(carrier_key, carrier_key)


def send_text(phone_number, carrier, message):
    smtp_host = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", "587"))
    smtp_username = os.getenv("MAIL_USERNAME")
    smtp_password = os.getenv("MAIL_PASSWORD")
    default_sender = os.getenv("MAIL_DEFAULT_SENDER", smtp_username)

    if not phone_number:
        raise ValueError("Phone number is required.")
    if not carrier:
        raise ValueError("Carrier is required.")
    if not message:
        raise ValueError("Message is required.")

    normalized_phone = normalize_phone_number(phone_number)
    if not normalized_phone:
        raise ValueError("Phone number is required.")

    carrier_key = normalize_carrier(carrier)
    domain = CARRIER_SMS_DOMAINS.get(carrier_key)
    if not domain:
        raise ValueError(f"Unsupported carrier: {carrier}")

    recipient = f"{normalized_phone}@{domain}"

    email = EmailMessage()
    email["Subject"] = ""  # SMS gateways usually ignore subject
    email["From"] = default_sender
    email["To"] = recipient
    email.set_content(message)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(email)