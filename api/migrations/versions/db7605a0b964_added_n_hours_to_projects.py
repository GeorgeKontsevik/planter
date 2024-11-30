"""added n_hours to projects

Revision ID: db7605a0b964
Revises: edb348d65113
Create Date: 2024-11-30 18:28:12.981116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'db7605a0b964'
down_revision: Union[str, None] = 'edb348d65113'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
