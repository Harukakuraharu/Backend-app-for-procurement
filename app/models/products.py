from decimal import Decimal

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.utils import intpk


category_product = Table(
    "category_product",
    Base.metadata,
    Column("category_id", ForeignKey("category.id"), primary_key=True),
    Column("product_id", ForeignKey("product.id"), primary_key=True),
)


class Category(Base):
    __tablename__ = "category"

    id: Mapped[intpk]
    title: Mapped[str]
    products: Mapped[list["Product"]] = relationship(
        back_populates="categories", lazy="joined", secondary=category_product
    )


class Product(Base):
    __tablename__ = "product"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(30))
    price: Mapped[Decimal]
    remainder: Mapped[int]
    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shop.id", ondelete="CASCADE")
    )
    shop: Mapped["Shop"] = relationship(  # type: ignore[name-defined]
        back_populates="products", lazy="joined"
    )
    categories: Mapped[list["Category"]] = relationship(
        back_populates="products", lazy="joined", secondary=category_product
    )


class Parametr(Base):
    __tablename__ = "parametr"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(15))


class ParametrProduct(Base):
    __tablename__ = "parametrproduct"

    id: Mapped[intpk]
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE")
    )
    parametr_id: Mapped[int] = mapped_column(
        ForeignKey("parametr.id", ondelete="CASCADE")
    )
    value: Mapped[str]
