"""add_outbox_table

Revision ID: 700000000000
Revises: 6577b5f961a0
Create Date: 2026-01-10 02:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '700000000000'
down_revision = '6577b5f961a0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create outbox table
    op.create_table(
        'outbox',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic', sa.String(length=255), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_outbox_status'), 'outbox', ['status'], unique=False)

    # Create trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION notify_outbox() RETURNS TRIGGER AS $$
        BEGIN
            PERFORM pg_notify('outbox_events', NEW.id::text);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger
    op.execute("""
        CREATE TRIGGER outbox_notify AFTER INSERT ON outbox
        FOR EACH ROW EXECUTE FUNCTION notify_outbox();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS outbox_notify ON outbox")
    op.execute("DROP FUNCTION IF EXISTS notify_outbox()")
    op.drop_index(op.f('ix_outbox_status'), table_name='outbox')
    op.drop_table('outbox')
