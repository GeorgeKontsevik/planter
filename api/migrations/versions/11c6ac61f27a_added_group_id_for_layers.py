"""added group_id for layers

Revision ID: 11c6ac61f27a
Revises: 6b25df109b2f
Create Date: 2024-12-19 16:34:39.934369

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '11c6ac61f27a'
down_revision: Union[str, None] = '6b25df109b2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('layers', sa.Column('group_name', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('layers', 'group_name')
    # ### end Alembic commands ###