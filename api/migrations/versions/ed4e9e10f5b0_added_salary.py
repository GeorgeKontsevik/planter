"""added salary

Revision ID: ed4e9e10f5b0
Revises: 697bb34eb5dc
Create Date: 2024-12-19 23:27:51.889101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'ed4e9e10f5b0'
down_revision: Union[str, None] = '697bb34eb5dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('layers', sa.Column('median_salary', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('layers', 'median_salary')
    # ### end Alembic commands ###
