"""Initial migration

Revision ID: 615ffe033a5c
Revises: 
Create Date: 2025-02-20 21:58:59.090678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '615ffe033a5c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('identifier', sa.String(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('createdAt', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('identifier')
    )

    # Create threads table
    op.create_table(
        'threads',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('createdAt', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('userId', postgresql.UUID(), nullable=True),
        sa.Column('userIdentifier', sa.String(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['userId'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create steps table
    op.create_table(
        'steps',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('threadId', postgresql.UUID(), nullable=False),
        sa.Column('parentId', postgresql.UUID(), nullable=True),
        sa.Column('disableFeedback', sa.Boolean(), nullable=True),
        sa.Column('streaming', sa.Boolean(), nullable=False),
        sa.Column('waitForAnswer', sa.Boolean(), nullable=True),
        sa.Column('isError', sa.Boolean(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('input', sa.String(), nullable=True),
        sa.Column('output', sa.String(), nullable=True),
        sa.Column('createdAt', sa.String(), nullable=True),
        sa.Column('start', sa.String(), nullable=True),
        sa.Column('end', sa.String(), nullable=True),
        sa.Column('generation', sa.JSON(), nullable=True),
        sa.Column('showInput', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('indent', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['threadId'], ['threads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create elements table
    op.create_table(
        'elements',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('threadId', postgresql.UUID(), nullable=True),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('chainlitKey', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('objectKey', sa.String(), nullable=True),
        sa.Column('size', sa.String(), nullable=True),
        sa.Column('page', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('forId', postgresql.UUID(), nullable=True),
        sa.Column('mime', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['threadId'], ['threads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create feedbacks table
    op.create_table(
        'feedbacks',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('forId', postgresql.UUID(), nullable=False),
        sa.Column('threadId', postgresql.UUID(), nullable=False),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.Column('comment', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['threadId'], ['threads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('feedbacks')
    op.drop_table('elements')
    op.drop_table('steps')
    op.drop_table('threads')
    op.drop_table('users')
