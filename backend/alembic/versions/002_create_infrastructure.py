"""Create infrastructure tables (SSH hosts, credentials, OIDC providers)

Revision ID: 002_create_infrastructure
Revises: 001_create_users_roles
Create Date: 2025-11-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_create_infrastructure'
down_revision = '001_create_users_roles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create SSHHost table
    op.create_table(
        'ssh_host',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('hostname', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False, server_default='22'),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('tags', sa.String(500), nullable=True),
        sa.Column('folder', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ssh_host_name'), 'ssh_host', ['name'], unique=False)

    # Create Credential table
    op.create_table(
        'credential',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('host_id', sa.String(36), nullable=False),
        sa.Column('credential_type', sa.String(50), nullable=False),
        sa.Column('encrypted_value', sa.Text(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('passphrase_encrypted', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['host_id'], ['ssh_host.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create OIDCProvider table
    op.create_table(
        'oidc_provider',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('discovery_url', sa.String(500), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('client_secret_encrypted', sa.Text(), nullable=False),
        sa.Column('redirect_uri', sa.String(500), nullable=False),
        sa.Column('scopes', sa.String(500), nullable=False, server_default='openid,profile,email'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(op.f('ix_oidc_provider_name'), 'oidc_provider', ['name'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_oidc_provider_name'), table_name='oidc_provider')
    op.drop_table('oidc_provider')
    op.drop_table('credential')
    op.drop_index(op.f('ix_ssh_host_name'), table_name='ssh_host')
    op.drop_table('ssh_host')
