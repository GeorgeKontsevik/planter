"""added n_hours to projects

Revision ID: edb348d65113
Revises: c49123cc6105
Create Date: 2024-11-30 18:19:58.260033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'edb348d65113'
down_revision: Union[str, None] = 'c49123cc6105'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
