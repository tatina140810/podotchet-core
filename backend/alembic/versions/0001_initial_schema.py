"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-11-14
"""
from alembic import op
import sqlalchemy as sa


revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('organizations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('plan', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('org_id', 'name', name='uq_categories_org_name')
    )
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_categories_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_categories_org_id'), ['org_id'], unique=False)

    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=200), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('supervisor_id', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['supervisor_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email', name='uq_users_email')
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=False)
        batch_op.create_index(batch_op.f('ix_users_org_id'), ['org_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_users_role'), ['role'], unique=False)
        batch_op.create_index(batch_op.f('ix_users_supervisor_id'), ['supervisor_id'], unique=False)

    op.create_table('expenses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('employee_id', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('spent_on', sa.Date(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('reviewed_by', sa.Integer(), nullable=True),
    sa.Column('review_comment', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
    sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['employee_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_expenses_category_id'), ['category_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_expenses_deleted_at'), ['deleted_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_expenses_employee_id'), ['employee_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_expenses_org_id'), ['org_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_expenses_spent_on'), ['spent_on'], unique=False)
        batch_op.create_index(batch_op.f('ix_expenses_status'), ['status'], unique=False)

    op.create_table('record_change_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('entity_type', sa.String(length=40), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(length=16), nullable=False),
    sa.Column('changed_by', sa.Integer(), nullable=False),
    sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('diff', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('record_change_log', schema=None) as batch_op:
        batch_op.create_index('ix_change_log_entity', ['org_id', 'entity_type', 'entity_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_record_change_log_org_id'), ['org_id'], unique=False)



def downgrade() -> None:
    with op.batch_alter_table('record_change_log', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_record_change_log_org_id'))
        batch_op.drop_index('ix_change_log_entity')

    op.drop_table('record_change_log')
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_expenses_status'))
        batch_op.drop_index(batch_op.f('ix_expenses_spent_on'))
        batch_op.drop_index(batch_op.f('ix_expenses_org_id'))
        batch_op.drop_index(batch_op.f('ix_expenses_employee_id'))
        batch_op.drop_index(batch_op.f('ix_expenses_deleted_at'))
        batch_op.drop_index(batch_op.f('ix_expenses_category_id'))

    op.drop_table('expenses')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_supervisor_id'))
        batch_op.drop_index(batch_op.f('ix_users_role'))
        batch_op.drop_index(batch_op.f('ix_users_org_id'))
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_categories_org_id'))
        batch_op.drop_index(batch_op.f('ix_categories_name'))

    op.drop_table('categories')
    op.drop_table('organizations')
