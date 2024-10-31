import datetime
import enum

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from models.utils import intpk


class OrderStatus(enum.Enum):
    CONFIRMED = "Подтвержден"
    ASSEMBLED = "Собран"
    SENT = "Отправлен"
    DELIVERED = "Доставлен"
    CANCELED = "Отменен"
    INPROGRES = "В обработке"


class Order(Base):
    __tablename__ = "order"

    id: Mapped[intpk]
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now()  # pylint: disable=E1102
    )
    status: Mapped[OrderStatus] = mapped_column(
        server_default=OrderStatus.INPROGRES.name,
        default=OrderStatus.INPROGRES,
    )


class ShoppingCart(Base):
    __tablename__ = "shoppingcart"

    id: Mapped[intpk]
    user: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE")
    )
    quantity: Mapped[int]
