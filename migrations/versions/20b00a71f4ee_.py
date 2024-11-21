"""empty message

Revision ID: 20b00a71f4ee
Revises: 3e804134d032
Create Date: 2024-11-21 13:01:19.097861

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20b00a71f4ee'
down_revision = '3e804134d032'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Document', schema=None) as batch_op:
        batch_op.add_column(sa.Column('state_id', sa.Integer(), nullable=False))
        batch_op.drop_constraint('Document_state_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'DocumentState', ['state_id'], ['id'])
        batch_op.drop_column('state')

    with op.batch_alter_table('DocumentEdit', schema=None) as batch_op:
        batch_op.add_column(sa.Column('state_id', sa.Integer(), nullable=False))
        batch_op.drop_constraint('DocumentEdit_state_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'DocumentEditState', ['state_id'], ['id'])
        batch_op.drop_column('state')

    with op.batch_alter_table('DocumentEditState', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type', sa.String(), nullable=False))
        batch_op.drop_constraint('DocumentEditState_state_key', type_='unique')
        batch_op.create_unique_constraint(None, ['type'])
        batch_op.drop_column('state')

    with op.batch_alter_table('DocumentRecommendation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('state_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(None, 'DocumentEditState', ['state_id'], ['id'])

    with op.batch_alter_table('DocumentState', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type', sa.String(), nullable=False))
        batch_op.drop_constraint('DocumentState_state_key', type_='unique')
        batch_op.create_unique_constraint(None, ['type'])
        batch_op.drop_column('state')

    with op.batch_alter_table('ModellingLanguage', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type', sa.String(), nullable=False))
        batch_op.drop_constraint('ModellingLanguage_name_key', type_='unique')
        batch_op.create_unique_constraint(None, ['type'])
        batch_op.drop_column('name')

    with op.batch_alter_table('Schema', schema=None) as batch_op:
        batch_op.add_column(sa.Column('modellingLanguage_id', sa.String(), nullable=False))
        batch_op.drop_constraint('Schema_modellingLanguage_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'ModellingLanguage', ['modellingLanguage_id'], ['id'])
        batch_op.drop_column('modellingLanguage')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Schema', schema=None) as batch_op:
        batch_op.add_column(sa.Column('modellingLanguage', sa.INTEGER(), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('Schema_modellingLanguage_fkey', 'ModellingLanguage', ['modellingLanguage'], ['id'])
        batch_op.drop_column('modellingLanguage_id')

    with op.batch_alter_table('ModellingLanguage', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='unique')
        batch_op.create_unique_constraint('ModellingLanguage_name_key', ['name'])
        batch_op.drop_column('type')

    with op.batch_alter_table('DocumentState', schema=None) as batch_op:
        batch_op.add_column(sa.Column('state', sa.VARCHAR(), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='unique')
        batch_op.create_unique_constraint('DocumentState_state_key', ['state'])
        batch_op.drop_column('type')

    with op.batch_alter_table('DocumentRecommendation', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('state_id')

    with op.batch_alter_table('DocumentEditState', schema=None) as batch_op:
        batch_op.add_column(sa.Column('state', sa.VARCHAR(), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='unique')
        batch_op.create_unique_constraint('DocumentEditState_state_key', ['state'])
        batch_op.drop_column('type')

    with op.batch_alter_table('DocumentEdit', schema=None) as batch_op:
        batch_op.add_column(sa.Column('state', sa.INTEGER(), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('DocumentEdit_state_fkey', 'DocumentEditState', ['state'], ['id'])
        batch_op.drop_column('state_id')

    with op.batch_alter_table('Document', schema=None) as batch_op:
        batch_op.add_column(sa.Column('state', sa.INTEGER(), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('Document_state_fkey', 'DocumentState', ['state'], ['id'])
        batch_op.drop_column('state_id')

    # ### end Alembic commands ###
