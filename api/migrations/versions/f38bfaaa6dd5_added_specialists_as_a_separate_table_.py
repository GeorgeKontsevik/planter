"""added specialists as a separate table related to project

Revision ID: f38bfaaa6dd5
Revises: 65c744f2131c
Create Date: 2024-12-01 00:02:05.034846

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'f38bfaaa6dd5'
down_revision: Union[str, None] = '65c744f2131c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
