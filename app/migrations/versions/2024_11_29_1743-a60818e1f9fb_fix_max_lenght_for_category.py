"""fix max lenght for category

Revision ID: a60818e1f9fb
Revises: 19af8d747d8c
Create Date: 2024-11-29 17:43:21.931740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a60818e1f9fb'
down_revision: Union[str, None] = '19af8d747d8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('category', 'title',
               existing_type=sa.VARCHAR(length=15),
               type_=sa.String(length=30),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('category', 'title',
               existing_type=sa.String(length=30),
               type_=sa.VARCHAR(length=15),
               existing_nullable=False)
    # ### end Alembic commands ###
