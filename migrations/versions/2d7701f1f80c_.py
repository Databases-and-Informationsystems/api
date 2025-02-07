"""empty message

Revision ID: 2d7701f1f80c
Revises: 511c4809eabc
Create Date: 2024-11-22 12:44:33.389123

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2d7701f1f80c"
down_revision = "511c4809eabc"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Document", schema=None) as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(), nullable=False))

    with op.batch_alter_table("User", schema=None) as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(), nullable=False))
        batch_op.create_unique_constraint(None, ["email"])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("User", schema=None) as batch_op:
        batch_op.drop_constraint(None, type_="unique")
        batch_op.drop_column("email")

    with op.batch_alter_table("Document", schema=None) as batch_op:
        batch_op.drop_column("name")

    # ### end Alembic commands ###
