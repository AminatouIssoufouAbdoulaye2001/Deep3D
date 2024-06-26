"""empty message

Revision ID: 9ac89b07f709
Revises: 382453063fdb
Create Date: 2024-04-19 17:31:16.983824

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9ac89b07f709'
down_revision = '382453063fdb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Conteneur', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date_creation', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Conteneur', schema=None) as batch_op:
        batch_op.drop_column('date_creation')

    # ### end Alembic commands ###
