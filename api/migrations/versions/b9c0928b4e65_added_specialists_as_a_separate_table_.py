"""added specialists as a separate table related to project

Revision ID: b9c0928b4e65
Revises: 952ec9462b32
Create Date: 2024-11-30 22:24:14.147681

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b9c0928b4e65'
down_revision: Union[str, None] = '952ec9462b32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_data_id', table_name='data')
    op.drop_table('data')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('data',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('key', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('value', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('project_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='data_project_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='data_pkey')
    )
    op.create_index('ix_data_id', 'data', ['id'], unique=False)
    # ### end Alembic commands ###
