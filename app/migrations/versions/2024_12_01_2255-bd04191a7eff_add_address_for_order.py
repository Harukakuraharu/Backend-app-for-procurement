"""add address for order

Revision ID: bd04191a7eff
Revises: c787b4d5956c
Create Date: 2024-12-01 22:55:59.383241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd04191a7eff'
down_revision: Union[str, None] = 'c787b4d5956c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('address_id', sa.Integer(), nullable=False))
    op.create_foreign_key(op.f('fk_orders_address_id_useraddress'), 'orders', 'useraddress', ['address_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('fk_orders_address_id_useraddress'), 'orders', type_='foreignkey')
    op.drop_column('orders', 'address_id')
    # ### end Alembic commands ###
