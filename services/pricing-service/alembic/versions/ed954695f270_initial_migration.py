"""initial_migration

Revision ID: ed954695f270
Revises:
Create Date: 2026-01-16 21:10:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ed954695f270'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create prices table
    op.create_table('prices',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('value', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('unit', sa.String(length=50), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('locked', sa.Boolean(), nullable=True),
    sa.Column('locked_by_saga_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prices_name'), 'prices', ['name'], unique=True)

    # Create outbox table
    op.create_table('outbox',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('topic', sa.String(length=255), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.Column('error_message', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_outbox_status'), 'outbox', ['status'], unique=False)

    # Add Postgres LISTEN/NOTIFY trigger
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_outbox() RETURNS TRIGGER AS $$
    BEGIN
      PERFORM pg_notify('outbox_events', NEW.id::text);
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER outbox_notify AFTER INSERT ON outbox
    FOR EACH ROW EXECUTE FUNCTION notify_outbox();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS outbox_notify ON outbox")
    op.execute("DROP FUNCTION IF EXISTS notify_outbox")
    op.drop_index(op.f('ix_outbox_status'), table_name='outbox')
    op.drop_table('outbox')
    op.drop_index(op.f('ix_prices_name'), table_name='prices')
    op.drop_table('prices')
