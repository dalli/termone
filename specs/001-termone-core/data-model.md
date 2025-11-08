# Phase 1 Design: Termone Data Model & Schema

**Date**: 2025-11-08
**Status**: Complete
**Purpose**: Define PostgreSQL schema, entities, relationships, and constraints

---

## Database Overview

**Database**: PostgreSQL 14+
**ORM**: SQLAlchemy 2.0+ (async driver: psycopg2[asyncpg])
**Migrations**: Alembic (schema versioning)

**Core Entities** (11 tables):
1. User, Role, Permission (Authentication & RBAC)
2. SSHHost, Credential (Infrastructure)
3. SSHSession, TerminalSession (State)
4. AuditLog (Compliance)
5. CommandSnippet, SSHTunnel (Features)
6. RefreshToken (Session extension)

---

## Entity Relationship Diagram

```
User (1) ----< (N) UserRole ----< (N) Role
  |                              |
  |----< (1:1) TOTPSecret        +--< (N) Permission
  |
  +----< (N) SSHHost
  |
  +----< (N) SSHSession
  |
  +----< (N) AuditLog
  |
  +----< (N) CommandSnippet
  |
  +----< (N) SSHTunnel

SSHHost (1) ----< (N) Credential
          ----< (N) SSHSession
          ----< (N) AuditLog (SFTP ops)
          ----< (N) SSHTunnel

SSHSession (1) ----< (N) TerminalSession
            ----< (N) AuditLog

Role (1) ----< (N) RolePermission ----< (N) Permission
     (1) ----< (N) HostGroupRole
     (1) ----< (N) UserRole

HostGroup (1) ----< (N) HostGroupHost ----< (N) SSHHost
          (1) ----< (N) HostGroupRole ----< (N) Role
```

---

## Core Tables

### 1. User

```sql
CREATE TABLE "user" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- NULL if SSO-only user
    username VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    oidc_provider_id VARCHAR(100),  -- e.g., 'google', 'okta'
    oidc_subject VARCHAR(500),      -- OpenID 'sub' claim (unique per provider)
    oidc_email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_oidc_identity UNIQUE (oidc_provider_id, oidc_subject),
    CONSTRAINT email_format CHECK (email ~ '^[^@]+@[^@]+\.[^@]+$'),
    CONSTRAINT username_length CHECK (length(username) >= 3)
);

CREATE INDEX idx_user_email ON "user"(email);
CREATE INDEX idx_user_username ON "user"(username);
CREATE INDEX idx_user_oidc ON "user"(oidc_provider_id, oidc_subject);
```

**Validations**:
- `email`: Valid email format, unique, max 255 chars
- `password_hash`: bcrypt hash (60 chars) if local auth
- `username`: 3-100 chars, alphanumeric + underscore, unique
- `oidc_subject`: Maps to external identity; unique per provider

---

### 2. TOTPSecret (2FA)

```sql
CREATE TABLE totp_secret (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES "user"(id) ON DELETE CASCADE,
    encrypted_secret VARCHAR(255) NOT NULL,  -- Base32-encoded, AES-encrypted
    verified BOOLEAN DEFAULT FALSE,
    backup_codes VARCHAR(255)[],             -- Encrypted array of backup codes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_totp_user_id ON totp_secret(user_id);
```

**Validations**:
- `encrypted_secret`: AES-256-GCM encrypted Base32 string (TOTP seed)
- One TOTP secret per user; NULL if 2FA disabled
- `backup_codes`: Array of 10 one-time-use codes for account recovery

---

### 3. Role

```sql
CREATE TABLE role (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_builtin BOOLEAN DEFAULT FALSE,  -- Built-in roles: Admin, User, ReadOnly
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT role_name_length CHECK (length(name) >= 2)
);

-- Built-in roles (inserted by seeder)
-- - Admin: Full access to all hosts and features
-- - User: Access to assigned hosts, can manage snippets and tunnels
-- - ReadOnly: View-only access to assigned hosts and stats
```

**Predefined Roles**:
```
Admin:
  - View all users and sessions
  - Configure OIDC providers
  - Manage roles and permissions
  - Delete any host or session

User (default):
  - Create/edit/delete own SSH hosts
  - Open terminal to own hosts
  - Manage own command snippets
  - Create tunnels to own hosts

ReadOnly:
  - View assigned hosts
  - View real-time stats (no terminal access)
  - No file manager access
```

---

### 4. Permission

```sql
CREATE TABLE permission (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'host.view', 'host.execute', 'host.delete'
    description TEXT,
    category VARCHAR(50),               -- 'host', 'file', 'user', 'admin'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT permission_name_length CHECK (length(name) >= 5)
);

-- Predefined permissions (sample)
-- - host.view: View host details
-- - host.execute: Execute commands via terminal/SFTP
-- - host.delete: Delete host
-- - host.edit: Edit host credentials
-- - file.upload: Upload files via SFTP
-- - file.download: Download files via SFTP
-- - file.delete: Delete remote files
-- - file.edit: Edit remote files
-- - user.view: View other users
-- - user.manage: Create/edit/delete users
-- - session.terminate: Force-terminate user sessions
```

---

### 5. UserRole (Many-to-Many)

```sql
CREATE TABLE user_role (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES role(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, role_id)
);

CREATE INDEX idx_user_role_user_id ON user_role(user_id);
CREATE INDEX idx_user_role_role_id ON user_role(role_id);
```

---

### 6. RolePermission (Many-to-Many)

```sql
CREATE TABLE role_permission (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES role(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permission(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(role_id, permission_id)
);

CREATE INDEX idx_role_permission_role_id ON role_permission(role_id);
CREATE INDEX idx_role_permission_permission_id ON role_permission(permission_id);
```

---

### 7. SSHHost

```sql
CREATE TABLE ssh_host (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),             -- IPv4 or IPv6
    port INTEGER NOT NULL DEFAULT 22,
    description TEXT,
    tags TEXT[],                        -- Array: ['production', 'database']
    folder_path VARCHAR(500),           -- Hierarchical: 'prod/databases/mysql-1'
    auth_type VARCHAR(20),              -- 'password' or 'key'
    username VARCHAR(100) DEFAULT 'root',
    default_shell VARCHAR(50) DEFAULT 'bash',  -- bash, sh, zsh, etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_connected_at TIMESTAMP,

    CONSTRAINT port_range CHECK (port > 0 AND port <= 65535),
    CONSTRAINT unique_host_per_user UNIQUE (owner_id, name),
    CONSTRAINT name_length CHECK (length(name) >= 1)
);

CREATE INDEX idx_ssh_host_owner_id ON ssh_host(owner_id);
CREATE INDEX idx_ssh_host_name ON ssh_host(name);
CREATE INDEX idx_ssh_host_tags ON ssh_host USING GIN(tags);
CREATE INDEX idx_ssh_host_folder_path ON ssh_host(folder_path);
```

**Validations**:
- `name`: Unique per user, 1-255 chars
- `hostname`: FQDN or IP, required
- `port`: 1-65535 range
- `tags`: Array for filtering/organization
- `folder_path`: Hierarchical path for tree structure
- `auth_type`: 'password' or 'key' (stored in Credential table)

---

### 8. Credential

```sql
CREATE TABLE credential (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ssh_host_id UUID NOT NULL UNIQUE REFERENCES ssh_host(id) ON DELETE CASCADE,
    auth_type VARCHAR(20) NOT NULL,     -- 'password' or 'key'
    encrypted_value TEXT NOT NULL,      -- AES-256-GCM encrypted
    key_type VARCHAR(20),               -- 'rsa', 'ed25519', 'ecdsa' (for key auth)
    key_fingerprint VARCHAR(255),       -- SHA256 fingerprint of public key
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT credential_auth_type CHECK (auth_type IN ('password', 'key'))
);

CREATE INDEX idx_credential_ssh_host_id ON credential(ssh_host_id);
```

**Encryption Details**:
- `encrypted_value`:
  - For password: AES-256-GCM(plaintext_password)
  - For SSH key: AES-256-GCM(plaintext_private_key_pem)
- Nonce stored alongside (prepended or stored separately)
- Decryption on-demand when opening terminal or SFTP

**Validation**:
- Never return unencrypted value in API responses
- Log: "Credential accessed for host_id=X" (without plaintext)

---

### 9. SSHSession

```sql
CREATE TABLE ssh_session (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    ssh_host_id UUID NOT NULL REFERENCES ssh_host(id) ON DELETE CASCADE,
    session_type VARCHAR(50) NOT NULL,  -- 'terminal', 'sftp', 'tunnel'
    status VARCHAR(20) NOT NULL,        -- 'active', 'idle', 'closed'
    token VARCHAR(500) NOT NULL,        -- JWT token for this session (short-lived)
    ip_address VARCHAR(45),
    user_agent TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    close_reason VARCHAR(255),          -- 'user_logout', 'timeout', 'error'

    CONSTRAINT status_values CHECK (status IN ('active', 'idle', 'closed'))
);

CREATE INDEX idx_ssh_session_user_id ON ssh_session(user_id);
CREATE INDEX idx_ssh_session_ssh_host_id ON ssh_session(ssh_host_id);
CREATE INDEX idx_ssh_session_status ON ssh_session(status);
CREATE INDEX idx_ssh_session_token ON ssh_session(token);
```

**Lifecycle**:
1. User clicks "Open Terminal" → SSHSession created with status='active'
2. Terminal active: WebSocket connected, last_activity_at updated on each interaction
3. Terminal idle (>5 min): status='idle' (server-side cleanup pending)
4. Terminal closed: status='closed', closed_at set, close_reason recorded

---

### 10. TerminalSession

```sql
CREATE TABLE terminal_session (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ssh_session_id UUID NOT NULL REFERENCES ssh_session(id) ON DELETE CASCADE,
    panel_id VARCHAR(50),               -- 'primary', 'split_1', 'split_2', 'split_3'
    rows INTEGER DEFAULT 24,
    cols INTEGER DEFAULT 80,
    theme VARCHAR(50) DEFAULT 'dracula',  -- 'dracula', 'solarized', 'monokai'
    font_family VARCHAR(100),
    font_size INTEGER DEFAULT 13,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT terminal_rows_range CHECK (rows > 0 AND rows <= 200),
    CONSTRAINT terminal_cols_range CHECK (cols > 0 AND cols <= 500)
);

CREATE INDEX idx_terminal_session_ssh_session_id ON terminal_session(ssh_session_id);
```

**Features**:
- Multiple panels in one session (up to 4)
- Each panel: independent theme, font, PTY dimensions
- Settings: Persisted to allow theme/font changes without restarting terminal

---

### 11. AuditLog

```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(100) NOT NULL,  -- 'auth.login', 'auth.failed', 'session.created', 'host.deleted', 'file.uploaded', etc.
    user_id UUID REFERENCES "user"(id) ON DELETE SET NULL,
    ssh_session_id UUID REFERENCES ssh_session(id) ON DELETE SET NULL,
    resource_type VARCHAR(50),         -- 'host', 'file', 'user', 'session'
    resource_id VARCHAR(255),
    action VARCHAR(50),                -- 'create', 'read', 'update', 'delete', 'execute'
    status VARCHAR(20),                -- 'success', 'failure', 'warning'
    result_message TEXT,               -- 'SSH authentication succeeded' or 'Permission denied'
    ip_address VARCHAR(45),
    user_agent TEXT,
    metadata JSONB,                    -- Flexible fields: {host_name, port, file_path, bytes_transferred, ...}

    CONSTRAINT event_type_not_empty CHECK (length(event_type) > 0)
);

CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_event_type ON audit_log(event_type);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_log_metadata ON audit_log USING GIN(metadata);

-- Partitioning by month for large-scale deployments
-- CREATE TABLE audit_log_2025_01 PARTITION OF audit_log FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

**Example Events**:
```json
{
  "event_type": "auth.login",
  "user_id": "uuid",
  "action": "login",
  "status": "success",
  "ip_address": "203.0.113.42",
  "metadata": {
    "auth_method": "oidc",
    "provider": "google",
    "mfa_enabled": true
  }
}

{
  "event_type": "terminal.execute",
  "user_id": "uuid",
  "ssh_session_id": "uuid",
  "resource_type": "host",
  "resource_id": "host-uuid",
  "action": "execute",
  "status": "success",
  "metadata": {
    "command": "ls -la",
    "output_lines": 42,
    "execution_ms": 250
  }
}

{
  "event_type": "file.upload",
  "user_id": "uuid",
  "resource_type": "file",
  "resource_id": "/home/user/myfile.txt",
  "action": "create",
  "status": "success",
  "metadata": {
    "bytes_uploaded": 102400,
    "file_type": "text",
    "duration_ms": 1500
  }
}
```

**Retention**: 90 days minimum (configurable, can be offloaded to external logging service after N days)

---

### 12. CommandSnippet

```sql
CREATE TABLE command_snippet (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    command TEXT NOT NULL,
    description TEXT,
    tags TEXT[],
    is_public BOOLEAN DEFAULT FALSE,   -- Shared with other users in same team?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_snippet_per_user UNIQUE (owner_id, name),
    CONSTRAINT name_length CHECK (length(name) >= 1),
    CONSTRAINT command_length CHECK (length(command) >= 1)
);

CREATE INDEX idx_command_snippet_owner_id ON command_snippet(owner_id);
CREATE INDEX idx_command_snippet_name ON command_snippet(name);
```

**Examples**:
```json
{
  "name": "Update Packages",
  "command": "sudo apt-get update && sudo apt-get upgrade -y"
}

{
  "name": "Check Docker Status",
  "command": "docker ps -a && docker images"
}

{
  "name": "View Logs",
  "command": "tail -f /var/log/application.log"
}
```

---

### 13. SSHTunnel

```sql
CREATE TABLE ssh_tunnel (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    ssh_host_id UUID NOT NULL REFERENCES ssh_host(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    tunnel_type VARCHAR(20) NOT NULL,  -- 'local' or 'remote'
    local_address VARCHAR(100),        -- '127.0.0.1' (only for local tunnels)
    local_port INTEGER,
    remote_address VARCHAR(255),       -- Target host/IP
    remote_port INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'inactive',  -- 'active', 'inactive', 'error'
    status_message TEXT,               -- 'Connection refused', 'Connected', etc.
    is_auto_reconnect BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_connected_at TIMESTAMP,

    CONSTRAINT unique_tunnel_per_user UNIQUE (owner_id, name),
    CONSTRAINT tunnel_type_check CHECK (tunnel_type IN ('local', 'remote')),
    CONSTRAINT port_range CHECK (local_port > 0 AND local_port <= 65535 AND remote_port > 0 AND remote_port <= 65535)
);

CREATE INDEX idx_ssh_tunnel_owner_id ON ssh_tunnel(owner_id);
CREATE INDEX idx_ssh_tunnel_ssh_host_id ON ssh_tunnel(ssh_host_id);
CREATE INDEX idx_ssh_tunnel_status ON ssh_tunnel(status);
```

**Types**:
- **Local Tunnel**: `localhost:8000 → remote_host:3306` (port forward from client to remote)
- **Remote Tunnel**: `remote_host:8080 → localhost:3000` (reverse port forward from remote to client)

---

### 14. RefreshToken (Optional, for Extended Sessions)

```sql
CREATE TABLE refresh_token (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,  -- SHA256(token)
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT token_length CHECK (length(token_hash) = 64)
);

CREATE INDEX idx_refresh_token_user_id ON refresh_token(user_id);
CREATE INDEX idx_refresh_token_expires_at ON refresh_token(expires_at);
```

**Purpose**: Allow users to refresh JWT tokens without re-entering credentials (optional feature for v1.1+)

---

## Constraints & Validations Summary

| Entity | Key Validation | Notes |
|--------|---|---|
| User | Unique email + username | No duplicate logins |
| SSHHost | Unique name per user | Users can name hosts independently |
| SSHSession | Foreign key + status enum | Ensures data integrity |
| Credential | Unique per host, encrypted | Only plaintext in memory |
| AuditLog | JSONB metadata | Flexible event logging |
| Terminal | Row/col limits (24-200, 80-500) | Prevent malformed PTY sizes |
| Tunnel | Port range validation | Standard SSH port rules |

---

## Indexes for Performance

**Query Patterns**:
1. **Auth**: `user.email`, `user.oidc_subject`
2. **Host List**: `ssh_host(owner_id, is_active)`
3. **Sessions**: `ssh_session(user_id, status)`
4. **Audit Search**: `audit_log(timestamp)`, `audit_log(event_type)`
5. **Snippets**: `command_snippet(owner_id, name)`

**Index Strategy**:
- B-tree for equality/range queries (email, user_id, status)
- GIN for array queries (tags) and JSON (metadata)
- Covering indexes for high-traffic queries (user_id + status)

---

## Future Enhancements

1. **SSH Key Rotation**: Add rotation history table and schedule
2. **Host Groups**: Share host access with teams (already designed: `HostGroup` + `HostGroupRole`)
3. **Session Recording**: Store terminal transcripts for audit
4. **Secrets Vault**: Migrate to external vault (Vault, AWS Secrets Manager)
5. **Multi-tenancy**: Add organization/workspace isolation

---

## SQL Initialization Script

**Location**: `backend/database/migrations/001_initial_schema.sql`

Alembic will manage this automatically, but raw SQL available for reference and backup.

**Steps**:
1. Create tables in dependency order (User → UserRole → SSHHost → Credential → etc.)
2. Create indexes
3. Insert predefined roles and permissions
4. (Optionally) seed test data if `APP_ENV=development`

---

## Conclusion

This schema supports all 6 core features and meets the Termone Constitution requirements for:
- **Security**: Encrypted credentials, audit logging, permission boundaries
- **API-First**: All entities queryable via REST/GraphQL
- **Test-First**: Clear models for unit/integration tests
- **Scalability**: Proper indexing for 100-1000 concurrent users

**Next Artifact**: API contracts (OpenAPI specifications) for all endpoints.
