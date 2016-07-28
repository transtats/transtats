"""create user table

Revision ID: 66cfc72df205
Revises: d874310748a9
Create Date: 2016-07-28 15:23:58.173573

"""

# revision identifiers, used by Alembic.
revision = '66cfc72df205'
down_revision = 'd874310748a9'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(200), unique=True, nullable=False),
        sa.Column('salt', sa.String(10)),
        sa.Column('password', sa.String(123)),
    )


def downgrade():
    op.drop_table('users')
