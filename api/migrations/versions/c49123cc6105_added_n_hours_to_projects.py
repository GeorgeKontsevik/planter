"""added n_hours to projects

Revision ID: c49123cc6105
Revises: 0e6d6a674136
Create Date: 2024-11-30 18:17:34.877647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'c49123cc6105'
down_revision: Union[str, None] = '0e6d6a674136'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
