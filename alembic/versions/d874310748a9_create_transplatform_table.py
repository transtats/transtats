"""create transplatform table

Revision ID: d874310748a9
Revises: 
Create Date: 2016-07-28 14:44:23.704206

"""

# revision identifiers, used by Alembic.
revision = 'd874310748a9'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'transplatform',
        sa.Column('platform_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('engine_name', sa.String(50), nullable=False),
        sa.Column('subject', sa.String(50)),
        sa.Column('api_url', sa.String(200)),
        sa.Column('platform_slug', sa.String(10), unique=True),
        sa.Column('server_status', sa.String(20)),
    )


def downgrade():
    op.drop_table('transplatform')
