"""add_index_to_registration

Revision ID: f3e74a45a435
Revises: 0a73d1811139
Create Date: 2024-10-28 05:48:10.834408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3e74a45a435'
down_revision: Union[str, None] = '0a73d1811139'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_registrations_event_id'), 'registrations', ['event_id'], unique=False)
    op.create_index(op.f('ix_registrations_visitor_id'), 'registrations', ['visitor_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_registrations_visitor_id'), table_name='registrations')
    op.drop_index(op.f('ix_registrations_event_id'), table_name='registrations')
    # ### end Alembic commands ###
