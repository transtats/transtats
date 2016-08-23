"""create locales table

Revision ID: b66f4ded9c02
Revises: 66cfc72df205
Create Date: 2016-08-03 18:08:10.833209

"""

# revision identifiers, used by Alembic.
revision = 'b66f4ded9c02'
down_revision = '66cfc72df205'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'locales',
        sa.Column('locale_id', sa.String(50), primary_key=True),
        sa.Column('lang_name', sa.String(200), unique=True),
        sa.Column('locale_alias', sa.String(50)),
        sa.Column('lang_status', sa.Boolean),
        sa.Column('lang_set', sa.String(50)),
    )


def downgrade():
    op.drop_table('locales')
