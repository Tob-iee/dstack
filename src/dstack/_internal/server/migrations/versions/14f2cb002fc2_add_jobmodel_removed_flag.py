"""Add JobModel.removed flag

Revision ID: 14f2cb002fc2
Revises: 112753bc17dd
Create Date: 2023-11-03 16:46:57.057973

"""

import sqlalchemy as sa
from alembic import op

from dstack._internal.core.models.runs import JobStatus

# revision identifiers, used by Alembic.
revision = "14f2cb002fc2"
down_revision = "112753bc17dd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("removed", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.add_column(sa.Column("remove_at", sa.DateTime(), nullable=True))

    # ### end Alembic commands ###
    op.execute(
        sa.sql.text("UPDATE jobs SET removed = TRUE WHERE status IN :statuses").bindparams(
            sa.bindparam("statuses", expanding=True),
            statuses=tuple(i.value.upper() for i in JobStatus.finished_statuses()),
        )
    )


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.drop_column("remove_at")
        batch_op.drop_column("removed")

    # ### end Alembic commands ###
