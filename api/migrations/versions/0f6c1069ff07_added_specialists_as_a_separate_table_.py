"""added specialists as a separate table related to project

Revision ID: 0f6c1069ff07
Revises: f5a8844146e2
Create Date: 2024-12-01 00:15:08.032789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '0f6c1069ff07'
down_revision: Union[str, None] = 'f5a8844146e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('specialists_specialty_key', 'specialists', type_='unique')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('specialists_specialty_key', 'specialists', ['specialty'])
    # ### end Alembic commands ###