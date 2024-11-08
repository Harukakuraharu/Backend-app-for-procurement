import datetime
import enum

from sqlalchemy import ForeignKey, String, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.utils import intpk


class UserStatus(enum.Enum):
    BUYER = "Покупатель"
    SHOP = "Магазин"
    MANAGER = "Менеджер"


class User(Base):
    __tablename__ = "user"

    id: Mapped[intpk]
    email: Mapped[str] = mapped_column(String(40), unique=True)
    password: Mapped[str] = mapped_column(String(72))
    name: Mapped[str] = mapped_column(String(15))
    status: Mapped[UserStatus]
    phone: Mapped[str]
    addresses: Mapped[list["UserAddress"]] = relationship(
        back_populates="user", lazy="joined"
    )
    shop: Mapped["Shop"] = relationship(back_populates="user", lazy="joined")


class Shop(Base):
    __tablename__ = "shop"

    id: Mapped[intpk]
    title: Mapped[str] = mapped_column(String(30))
    url: Mapped[str]
    active: Mapped[bool] = mapped_column(server_default=false())
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now()  # pylint: disable=E1102
    )
    # pylint: disable=C0301
    products: Mapped[list["Product"]] = relationship(  # type: ignore[name-defined]
        back_populates="shop", lazy="selectin"
    )
    user: Mapped[User] = relationship(back_populates="shop", lazy="joined")


class UserAddress(Base):
    __tablename__ = "useraddress"

    id: Mapped[intpk]
    city: Mapped[str]
    address: Mapped[str]
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    user: Mapped[User] = relationship(
        back_populates="addresses", lazy="selectin"
    )
