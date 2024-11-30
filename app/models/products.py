from decimal import Decimal

from sqlalchemy import CheckConstraint, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.utils import intpk


category_product = Table(
    "category_product",
    Base.metadata,
    Column(
        "category_id",
        ForeignKey("category.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "product_id",
        ForeignKey("product.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Category(Base):
    __tablename__ = "category"

    id: Mapped[intpk]
    title: Mapped[str] = mapped_column(String(100), unique=True)
    products: Mapped[list["Product"]] = relationship(
        back_populates="categories",
        lazy="selectin",
        secondary=category_product,
    )


class Product(Base):
    __tablename__ = "product"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal]
    remainder: Mapped[int]
    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shop.id", ondelete="CASCADE")
    )
    shop: Mapped["Shop"] = relationship(  # type: ignore[name-defined]
        back_populates="products", lazy="joined"
    )
    categories: Mapped[list[Category]] = relationship(
        back_populates="products", lazy="selectin", secondary=category_product
    )
    parametrs: Mapped[list["ParametrProduct"]] = relationship(
        back_populates="product", lazy="selectin"
    )
    # pylint: disable=C0301
    orderlist: Mapped[list["OrderList"]] = relationship(  # type: ignore[name-defined]
        back_populates="product", lazy="selectin"
    )
    __table_args__ = (CheckConstraint("remainder > 0", name="remainder_gt_0"),)

    def __repr__(self) -> str:
        return (
            f"product_id - {self.id}, "
            f"name - {self.name}, "
            f"remainder - {self.remainder}, "
            f"shop_id - {self.shop_id}"
        )


class Parametr(Base):
    __tablename__ = "parametr"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(100), unique=True)


class ParametrProduct(Base):
    __tablename__ = "parametrproduct"

    id: Mapped[intpk]
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE")
    )
    product: Mapped[Product] = relationship(
        back_populates="parametrs", lazy="joined"
    )
    parametr_id: Mapped[int] = mapped_column(
        ForeignKey("parametr.id", ondelete="CASCADE")
    )
    value: Mapped[str]
