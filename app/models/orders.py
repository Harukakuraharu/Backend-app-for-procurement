import datetime
import enum

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.utils import intpk


class OrderStatus(enum.Enum):
    CONFIRMED = "Подтвержден"
    ASSEMBLED = "Собран"
    SENT = "Отправлен"
    DELIVERED = "Доставлен"
    CANCELED = "Отменен"
    INPROGRES = "В обработке"
    SHOPPINGCART = "Корзина"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    # pylint: disable=C0301
    user: Mapped["User"] = relationship(back_populates="orders", lazy="joined")  # type: ignore[name-defined]
    status: Mapped[OrderStatus]
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now()  # pylint: disable=E1102
    )
    orderlist: Mapped[list["OrderList"]] = relationship(
        back_populates="order", lazy="selectin"
    )
    address_id: Mapped[int] = mapped_column(
        ForeignKey("useraddress.id", ondelete="CASCADE")
    )
    address: Mapped["UserAddress"] = relationship(  # type: ignore[name-defined]
        back_populates="order", lazy="joined"
    )


class OrderList(Base):
    __tablename__ = "orderlist"

    id: Mapped[intpk]
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE")
    )
    product: Mapped["Product"] = relationship(  # type: ignore[name-defined]
        back_populates="orderlist", lazy="selectin"
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE")
    )
    order: Mapped[Order] = relationship(
        back_populates="orderlist", lazy="joined"
    )
    quantity: Mapped[int]
