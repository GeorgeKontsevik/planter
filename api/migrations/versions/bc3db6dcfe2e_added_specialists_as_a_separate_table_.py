"""added specialists as a separate table related to project

Revision ID: bc3db6dcfe2e
Revises: 8b69ad7bd65c
Create Date: 2024-11-30 23:26:09.215522

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'bc3db6dcfe2e'
down_revision: Union[str, None] = '8b69ad7bd65c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('specialists', sa.Column('count', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('specialists', 'count')
    # ### end Alembic commands ###