"""create jobs syncstats tables

Revision ID: 20f167444052
Revises: 5ffd170eed2e
Create Date: 2016-08-24 17:12:41.202864

"""

# revision identifiers, used by Alembic.
revision = '20f167444052'
down_revision = '5ffd170eed2e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql.json import JSONB


def upgrade():
    op.create_table(
        'jobs',
        sa.Column('job_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('job_uuid', UUID(as_uuid=True), unique=True, nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('job_start_time', sa.DateTime),
        sa.Column('job_end_time', sa.DateTime),
        sa.Column('job_log_json', JSONB),
        sa.Column('job_result', sa.String(50)),
        sa.Column('job_remarks', sa.String(200)),
    )

    op.create_table(
        'syncstats',
        sa.Column('sync_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('package_name', sa.String(200), sa.ForeignKey('packages.package_name')),
        sa.Column('job_uuid', UUID(as_uuid=True), sa.ForeignKey('jobs.job_uuid')),
        sa.Column('project_version', sa.String(200)),
        sa.Column('stats_raw_json', JSONB),
        sa.Column('sync_iter_count', sa.Integer),
        sa.Column('sync_visibility', sa.Boolean),
    )


def downgrade():
    op.drop_table('syncstats')
    op.drop_table('jobs')
