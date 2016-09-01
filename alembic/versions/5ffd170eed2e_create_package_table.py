"""create package table

Revision ID: 5ffd170eed2e
Revises: ff05a9f5bde8
Create Date: 2016-08-08 12:22:12.169136

"""

# revision identifiers, used by Alembic.
revision = '5ffd170eed2e'
down_revision = 'ff05a9f5bde8'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql.json import JSONB


def upgrade():
    op.create_table(
        'packages',
        sa.Column('package_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('package_name', sa.String(200), unique=True, nullable=False),
        sa.Column('upstream_url', sa.String(500), nullable=False),
        sa.Column('transplatform_slug', sa.String(10)),
        sa.Column('transplatform_url', sa.String(500)),
        sa.Column('release_streams', ARRAY(sa.String(100)), default=[]),
        sa.Column('lang_set', sa.String(50)),
        sa.Column('transtats_lastupdated', sa.DateTime, nullable=True),
        sa.Column('package_details_json', JSONB, nullable=True),
        sa.Column('details_json_lastupdated', sa.DateTime, nullable=True)
    )


def downgrade():
    op.drop_table('packages')
