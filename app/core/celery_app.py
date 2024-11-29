import smtplib
import ssl
from email.message import EmailMessage

from celery import Celery

from core.settings import config


celery_app = Celery(
    broker_url=config.celery_url,
    broker_connection_retry_on_startup=True,
    include=["core.celery_app"],
)


@celery_app.task
def send_email(data):
    """Send email"""
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(
        config.CORP_HOST, config.CORP_PORT, context=context
    ) as server:
        msg = EmailMessage()
        msg.set_content(data["msg"])
        msg["Subject"] = data["subject"]
        server.login(config.CORP_EMAIL, config.CORP_KEY)
        server.send_message(msg, config.CORP_EMAIL, data["emails"])
