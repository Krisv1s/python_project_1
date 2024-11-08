"""Create events, visitors and registration tables

Revision ID: 8b384f6914df
Revises: 
Create Date: 2024-10-26 17:19:13.816268

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b384f6914df'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=255), server_default='planning', nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('start_at', sa.DateTime(), nullable=False),
    sa.Column('location', sa.String(length=255), nullable=False),
    sa.Column('end_at', sa.DateTime(), nullable=False),
    sa.Column('price', sa.Integer(), nullable=False),
    sa.Column('visitor_limit', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)
    op.create_index(op.f('ix_events_title'), 'events', ['title'], unique=False)
    op.create_table('visitors',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('first_name', sa.String(length=255), nullable=False),
    sa.Column('last_name', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('phone')
    )
    op.create_index(op.f('ix_visitors_id'), 'visitors', ['id'], unique=False)
    op.create_table('registrations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('visitor_id', sa.Integer(), nullable=True),
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=255), server_default='unpaid', nullable=False),
    sa.Column('price', sa.Integer(), nullable=True),
    sa.Column('billed_amount', sa.Integer(), nullable=True),
    sa.Column('refund_amount', sa.Integer(), nullable=True),
    sa.Column('billed_at', sa.TIMESTAMP(), nullable=True),
    sa.Column('refunded_at', sa.TIMESTAMP(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
    sa.ForeignKeyConstraint(['visitor_id'], ['visitors.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_registrations_id'), 'registrations', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_registrations_id'), table_name='registrations')
    op.drop_table('registrations')
    op.drop_index(op.f('ix_visitors_id'), table_name='visitors')
    op.drop_table('visitors')
    op.drop_index(op.f('ix_events_title'), table_name='events')
    op.drop_index(op.f('ix_events_id'), table_name='events')
    op.drop_table('events')
    # ### end Alembic commands ###