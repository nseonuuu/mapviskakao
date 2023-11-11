"""Initial migration.

Revision ID: 2f415a1e355b
Revises: 
Create Date: 2023-11-11 12:55:11.843014

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f415a1e355b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('past_comment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date_posted', sa.DateTime(), nullable=False))
        batch_op.add_column(sa.Column('date_moved', sa.DateTime(), nullable=True))
        batch_op.alter_column('content',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('past_comment', schema=None) as batch_op:
        batch_op.alter_column('content',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
        batch_op.drop_column('date_moved')
        batch_op.drop_column('date_posted')

    # ### end Alembic commands ###
