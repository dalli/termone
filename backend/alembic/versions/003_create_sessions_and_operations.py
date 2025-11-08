"""Create sessions and operations tables

Revision ID: 003_create_sessions_and_operations
Revises: 002_create_infrastructure
Create Date: 2025-11-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_create_sessions_and_operations'
down_revision = '002_create_infrastructure'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create SSHSession table
    op.create_table(
        'ssh_session',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('host_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('session_key', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['host_id'], ['ssh_host.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_key'),
    )
    op.create_index(op.f('ix_ssh_session_host_id'), 'ssh_session', ['host_id'], unique=False)
    op.create_index(op.f('ix_ssh_session_session_key'), 'ssh_session', ['session_key'], unique=True)

    # Create TerminalSession table
    op.create_table(
        'terminal_session',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('host_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('session_key', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.Column('pty_rows', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('pty_cols', sa.Integer(), nullable=False, server_default='80'),
        sa.Column('terminal_type', sa.String(50), nullable=False, server_default='xterm-256color'),
        sa.Column('shell', sa.String(255), nullable=False, server_default='/bin/bash'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['host_id'], ['ssh_host.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_key'),
    )
    op.create_index(op.f('ix_terminal_session_host_id'), 'terminal_session', ['host_id'], unique=False)
    op.create_index(op.f('ix_terminal_session_session_key'), 'terminal_session', ['session_key'], unique=True)

    # Create AuditLog table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('host_id', sa.String(36), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['host_id'], ['ssh_host.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_log_action'), 'audit_log', ['action'], unique=False)
    op.create_index(op.f('ix_audit_log_timestamp'), 'audit_log', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_log_user_id'), 'audit_log', ['user_id'], unique=False)

    # Create CommandSnippet table
    op.create_table(
        'command_snippet',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('command', sa.Text(), nullable=False),
        sa.Column('tags', sa.String(500), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_command_snippet_user_id'), 'command_snippet', ['user_id'], unique=False)

    # Create SSHTunnel table
    op.create_table(
        'ssh_tunnel',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('host_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('tunnel_type', sa.String(50), nullable=False),
        sa.Column('local_bind_host', sa.String(255), nullable=True),
        sa.Column('local_bind_port', sa.Integer(), nullable=False),
        sa.Column('remote_bind_host', sa.String(255), nullable=False),
        sa.Column('remote_bind_port', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('last_connection_time', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['host_id'], ['ssh_host.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ssh_tunnel_host_id'), 'ssh_tunnel', ['host_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ssh_tunnel_host_id'), table_name='ssh_tunnel')
    op.drop_table('ssh_tunnel')
    op.drop_index(op.f('ix_command_snippet_user_id'), table_name='command_snippet')
    op.drop_table('command_snippet')
    op.drop_index(op.f('ix_audit_log_user_id'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_timestamp'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_action'), table_name='audit_log')
    op.drop_table('audit_log')
    op.drop_index(op.f('ix_terminal_session_session_key'), table_name='terminal_session')
    op.drop_index(op.f('ix_terminal_session_host_id'), table_name='terminal_session')
    op.drop_table('terminal_session')
    op.drop_index(op.f('ix_ssh_session_session_key'), table_name='ssh_session')
    op.drop_index(op.f('ix_ssh_session_host_id'), table_name='ssh_session')
    op.drop_table('ssh_session')
