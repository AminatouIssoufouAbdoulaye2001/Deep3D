"""empty message

Revision ID: 33828a5f4f5a
Revises: 
Create Date: 2024-04-06 03:21:49.287291

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '33828a5f4f5a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Supprime la colonne 'adresse' existante
    with op.batch_alter_table('User', schema=None) as batch_op:
        batch_op.drop_column('adresse')

def downgrade():
    # Ajoute la colonne 'adresse' de nouveau
    with op.batch_alter_table('User', schema=None) as batch_op:
        batch_op.add_column(sa.Column('adresse', sa.String(length=255), nullable=True))


