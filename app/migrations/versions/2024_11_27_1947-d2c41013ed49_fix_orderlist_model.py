"""fix orderlist model

Revision ID: d2c41013ed49
Revises: 29551ea88771
Create Date: 2024-11-27 19:47:52.058332

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2c41013ed49'
down_revision: Union[str, None] = '29551ea88771'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orderlist', sa.Column('order_id', sa.Integer(), nullable=False))
    op.create_foreign_key(op.f('fk_orderlist_order_id_orders'), 'orderlist', 'orders', ['order_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('fk_orderlist_order_id_orders'), 'orderlist', type_='foreignkey')
    op.drop_column('orderlist', 'order_id')
    # ### end Alembic commands ###