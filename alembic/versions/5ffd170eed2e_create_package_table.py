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


def upgrade():
    op.create_table(
        'packages',
        sa.Column('package_id', sa.Integer, primary_key=True),
        sa.Column('package_name', sa.String(200), unique=True, nullable=False),
        sa.Column('upstream_url', sa.String(200), unique=True, nullable=False),
        sa.Column('transplatform_slug', sa.String(10)),
        sa.Column('transplatform_url', sa.String(200)),
        sa.Column('release_stream_slug', sa.String(10)),
        sa.Column('lang_set', sa.String(50)),
        sa.Column('transtats_lastupdated', sa.DateTime),
    )


def downgrade():
    op.drop_table('packages')
