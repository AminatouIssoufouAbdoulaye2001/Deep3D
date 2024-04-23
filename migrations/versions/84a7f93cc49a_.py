"""empty message

Revision ID: 84a7f93cc49a
Revises: 30c84470e0a2
Create Date: 2024-04-22 18:07:39.979526

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '84a7f93cc49a'
down_revision = '30c84470e0a2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Article', schema=None) as batch_op:
        batch_op.alter_column('date_creation',
               existing_type=sa.DATETIME(),
               type_=sa.Date(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Article', schema=None) as batch_op:
        batch_op.alter_column('date_creation',
               existing_type=sa.Date(),
               type_=sa.DATETIME(),
               existing_nullable=True)

    # ### end Alembic commands ###
