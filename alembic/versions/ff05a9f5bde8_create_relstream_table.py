"""create relstream table

Revision ID: ff05a9f5bde8
Revises: b66f4ded9c02
Create Date: 2016-08-04 12:20:46.340753

"""

# revision identifiers, used by Alembic.
revision = 'ff05a9f5bde8'
down_revision = 'b66f4ded9c02'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'relstream',
        sa.Column('relstream_id', sa.Integer, primary_key=True),
        sa.Column('relstream_name', sa.String(50)),
        sa.Column('relstream_slug', sa.String(10), unique=True),
        sa.Column('relstream_server', sa.String(200), unique=True),
        sa.Column('relstream_built', sa.String(10)),
        sa.Column('srcpkg_format', sa.String(10)),
        sa.Column('top_url', sa.String(200)),
        sa.Column('web_url', sa.String(200)),
        sa.Column('krb_service', sa.String(50)),
        sa.Column('auth_type', sa.String(50)),
        sa.Column('amqp_server', sa.String(200)),
        sa.Column('msgbus_exchange', sa.String(20)),
        sa.Column('relstream_status', sa.String(10)),
    )


def downgrade():
    op.drop_table('relstream')
