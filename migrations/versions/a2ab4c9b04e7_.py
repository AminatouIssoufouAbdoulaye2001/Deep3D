"""empty message

Revision ID: a2ab4c9b04e7
Revises: 9e4e8dcccea5
Create Date: 2024-06-14 16:42:28.003750

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2ab4c9b04e7'
down_revision = '9e4e8dcccea5'
branch_labels = None
depends_on = None


def upgrade():
    # ... autres opérations de migration ...
    with op.batch_alter_table('Commande', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=False, server_default='En attente'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Commande', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###