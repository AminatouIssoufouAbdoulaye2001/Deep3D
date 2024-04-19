"""empty message

Revision ID: 519ebaa19bbf
Revises: 9e71140b41ec
Create Date: 2024-04-19 15:17:35.361309

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '519ebaa19bbf'
down_revision = '9e71140b41ec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Commande', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Commande', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###
