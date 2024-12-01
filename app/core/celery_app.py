import smtplib
import ssl
from email.message import EmailMessage

import sqlalchemy as sa
import yaml
from celery import Celery
from sqlalchemy.orm import Session

import models
from api import crud
from core.settings import config


engine = sa.create_engine(config.dsn)  # type: ignore[call-overload]

celery_app = Celery(
    broker_url=config.celery_url,
    broker_connection_retry_on_startup=True,
    include=["core.celery_app"],
)


@celery_app.task
def send_email(data: dict):
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


@celery_app.task
def products_import(contents: bytes, user_id: int):
    with Session(bind=engine) as session:
        data = yaml.safe_load(contents)
        user = crud.sync_get_item_id(session, models.User, user_id)
        if not user.shop:
            shop = crud.sync_create_item(
                session,
                {"title": data["shop"], "user_id": user.id},
                models.Shop,
            )
            shop.active = True
            session.flush()
            user.shop = shop
        shop_id = user.shop.id  # type: ignore[union-attr]
        for product in data["goods"]:
            parameters = product.pop("parameters")
            categories = product.pop("category")
            product["shop_id"] = shop_id
            product_db = crud.sync_create_item(
                session, product, models.Product
            )
            session.flush()
            for parametr, value in parameters.items():
                parametr_db = session.scalar(
                    sa.select(models.Parametr).where(
                        models.Parametr.name == parametr
                    )
                )
                if not parametr_db:
                    parametr_db = crud.sync_create_item(
                        session, {"name": parametr}, models.Parametr
                    )
                    session.flush()
                crud.sync_create_item(
                    session,
                    {
                        "product_id": product_db.id,
                        # pylint: disable=C0301
                        "parametr_id": parametr_db.id,  # type: ignore[union-attr]
                        "value": value,
                    },
                    models.ParametrProduct,
                )
            session.commit()
            session.refresh(product_db)

            category_db = session.scalar(
                sa.select(models.Category).where(
                    models.Category.title == categories
                )
            )
            if not category_db:
                category_db = crud.sync_create_item(
                    session, {"title": categories}, models.Category
                )
                session.flush()
            product_db.categories = [category_db]
        session.commit()
