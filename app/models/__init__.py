from typing import Type, TypeVar

from models.base import Base
from models.orders import Order, OrderStatus, ShoppingCart
from models.products import Category, Parametr, ParametrProduct, Product
from models.users import Shop, User, UserAddress, UserStatus


MODEL = TypeVar("MODEL", bound=Base)

TypeModel = Type[MODEL]
