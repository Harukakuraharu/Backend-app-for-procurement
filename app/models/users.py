import datetime
import enum

from sqlalchemy import ForeignKey, String, false, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.utils import intpk


class UserStatus(enum.Enum):
    BUYER = "Покупатель"
    SHOP = "Магазин"
    MANAGER = "Менеджер"


class User(Base):
    __tablename__ = "users"

    id: Mapped[intpk]
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(72))
    name: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[UserStatus]
    phone: Mapped[str | None]
    addresses: Mapped[list["UserAddress"]] = relationship(
        back_populates="user", lazy="joined"
    )
    shop: Mapped["Shop"] = relationship(back_populates="user", lazy="joined")
    orders: Mapped[list["Order"]] = relationship(  # type: ignore[name-defined]
        back_populates="user", lazy="selectin"
    )
    active: Mapped[bool] = mapped_column(server_default=false())


class Shop(Base):
    __tablename__ = "shop"

    id: Mapped[intpk]
    title: Mapped[str] = mapped_column(String(100))
    url: Mapped[str | None]
    active: Mapped[bool] = mapped_column(server_default=true())
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now()  # pylint: disable=E1102
    )
    # pylint: disable=C0301
    products: Mapped[list["Product"]] = relationship(  # type: ignore[name-defined]
        back_populates="shop", lazy="selectin"
    )
    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        back_populates="shop", lazy="joined"
    )


class UserAddress(Base):
    __tablename__ = "useraddress"

    id: Mapped[intpk]
    city: Mapped[str]
    address: Mapped[str]
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    user: Mapped[User] = relationship(
        back_populates="addresses", lazy="selectin"
    )
    order: Mapped[list["Order"]] = relationship(  # type: ignore[name-defined]
        back_populates="address", lazy="joined"
    )
