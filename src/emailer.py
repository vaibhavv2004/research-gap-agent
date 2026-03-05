import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .config import TO_EMAIL, FROM_EMAIL


def send_email(subject: str, body_text: str, body_html: str) -> None:
    gmail_user = os.getenv("GMAIL_USER", "")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD", "")

    if not gmail_user or not gmail_pass:
        raise ValueError("Missing GMAIL_USER or GMAIL_APP_PASSWORD in .env")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL or gmail_user
    msg["To"] = TO_EMAIL

    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_pass)
        server.sendmail(msg["From"], [TO_EMAIL], msg.as_string())