# Feature Specification: Termone - Web-Based SSH Infrastructure Management Platform

**Feature Branch**: `001-termone-core`
**Created**: 2025-11-08
**Status**: Draft
**Input**: Complete product specification for termone project

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Admin Dashboard and Host Management (Priority: P1)

An administrator logs into Termone, views a dashboard with frequently accessed hosts, active tunnel status, and server resource summaries. They can register new SSH hosts with credentials (password or private key), organize them using tags and folders, and search/filter across hundreds of hosts efficiently.

**Why this priority**: Core foundation - enables all other features. Must exist before terminal access, file management, or monitoring.

**Independent Test**: Can be tested by verifying: Admin can login → Register host with password auth → Register host with SSH key auth → Search/filter hosts → Dashboard displays data → Independent of terminal/file features.

**Acceptance Scenarios**:

1. **Given** admin is on dashboard, **When** they access the host manager, **Then** they see a list of registered hosts organized by tags/folders
2. **Given** admin wants to add a host, **When** they fill hostname, IP, port, auth credentials, **Then** host is encrypted and stored in DB
3. **Given** admin has registered hosts with SSH keys, **When** they select multiple hosts, **Then** they can batch-deploy their public key to authorized_keys
4. **Given** admin searches for hosts, **When** they type a hostname/tag, **Then** matching hosts appear within 500ms
5. **Given** multiple admins are logged in, **When** one admin registers a new host, **Then** other admins see the update within 2 seconds (via WebSocket)

---

### User Story 2 - SSH Terminal Access (Priority: P1)

A user connects to a registered SSH host from the browser terminal. They interact with a full PTY shell (bash/sh) in real-time, execute commands, view output, and can open multiple terminal sessions via tabs. They can split a single tab into up to 4 panels, customize terminal themes and fonts, and their session persists across brief network interruptions.

**Why this priority**: Core user-facing feature. SSH terminal is the primary use case for this platform. Required before file manager or server monitoring can be tested.

**Independent Test**: Can be tested by verifying: User selects a host → Opens terminal → Executes commands → Receives output → Can open multiple sessions → Tabs work independently. Does not require host manager or file manager for basic testing.

**Acceptance Scenarios**:

1. **Given** user is on host page, **When** they click "Open Terminal", **Then** WebSocket connects and PTY shell spawns within 2 seconds
2. **Given** user has terminal open, **When** they type a command, **Then** output appears within 100ms (latency)
3. **Given** user has multiple terminal tabs, **When** they close one tab, **Then** that SSH session is properly closed; other tabs remain unaffected
4. **Given** user opens a terminal with 4-panel layout, **When** they execute different commands in each panel, **Then** each panel independently streams output
5. **Given** user's browser connection drops, **When** reconnection happens within 30 seconds, **Then** terminal session is restored without re-authentication
6. **Given** user switches terminal themes (Dracula, Solarized), **When** they refresh the page, **Then** chosen theme persists

---

### User Story 3 - Server Monitoring and Real-time Stats (Priority: P1)

A user opens a host's stats page and sees real-time CPU usage, memory consumption, disk space, network traffic, uptime, and system info (OS, kernel version) displayed as charts and text. Data refreshes every 5 seconds via WebSocket. The backend periodically executes system commands (vmstat, df, free, etc.) via SSH and streams results.

**Why this priority**: P1 feature for infrastructure monitoring. Completes the dashboard MVP alongside terminal and file manager.

**Independent Test**: Can be tested by verifying: User opens stats page → Data loads → Charts update in real-time → Data persists across page refreshes. Does not depend on terminal or file manager.

**Acceptance Scenarios**:

1. **Given** user opens a host's stats page, **When** page loads, **Then** charts display current CPU, memory, disk usage within 3 seconds
2. **Given** backend is collecting stats every 5 seconds, **When** 10 seconds pass, **Then** charts have ≥2 data points and show trend
3. **Given** user leaves stats page open for 5 minutes, **When** they return, **Then** system info (OS, kernel) and uptime are current
4. **Given** backend collects stats via SSH, **When** SSH connection drops, **Then** stats collection retries after 30 seconds; user sees "disconnected" state
5. **Given** user has multiple hosts open in separate tabs, **When** each host's stats refresh independently, **Then** no cross-contamination of data

---

### User Story 4 - Remote File Management via SFTP (Priority: P2)

A user opens the remote file manager for a host, navigates directories via SFTP, uploads/downloads files (drag-and-drop supported), renames/deletes/moves files, and changes permissions (chmod). For text/code files, they can edit inline using an embedded Monaco editor. For media (images, audio, video), they can preview directly in the browser.

**Why this priority**: P2 - Important for full infrastructure management, but file uploads/downloads can be done via terminal. Adds usability for non-CLI users.

**Independent Test**: Can be tested independently by verifying: User opens file manager → Navigates directories → Uploads file → Downloads file → Edits text file → Views image → Deletes file. Does not require terminal or monitoring features.

**Acceptance Scenarios**:

1. **Given** user opens file manager for a host, **When** they request directory listing, **Then** files load within 2 seconds via SFTP
2. **Given** user drags a file to the upload zone, **When** upload completes, **Then** file appears in directory listing
3. **Given** user has a text file selected, **When** they click "Edit", **Then** Monaco editor opens with file content
4. **Given** user modifies code and clicks "Save", **When** save completes, **Then** file is updated on remote server
5. **Given** user views an image file, **When** image loads, **Then** thumbnail and full preview display correctly
6. **Given** user changes a file's permission to 755, **When** change applies, **Then** file's chmod is updated on server

---

### User Story 5 - SSH Tunnel Management (Priority: P2)

A user configures local port forwarding (localhost:8000 → remote:3306) or remote port forwarding to create tunnels. They can view active tunnel status, see which tunnel is connected/disconnected, and the system automatically reconnects if tunnel drops.

**Why this priority**: P2 - Useful for accessing remote databases, services, but can be done via command-line SSH as fallback.

**Independent Test**: Can be tested independently by verifying: User creates local tunnel → Tunnel appears in list → Can connect to forwarded port → Tunnel reconnects on failure. Does not require terminal, file manager, or stats.

**Acceptance Scenarios**:

1. **Given** user creates a local port forward (localhost:8000 → remote:3306), **When** tunnel activates, **Then** user can connect to localhost:8000
2. **Given** tunnel is active, **When** remote server disconnects, **Then** tunnel shows "disconnected" status and auto-reconnects within 30 seconds
3. **Given** user has multiple tunnels active, **When** one tunnel fails, **Then** other tunnels remain unaffected

---

### User Story 6 - SSH Command Snippets (Priority: P3)

A user saves frequently used commands as snippets (e.g., "Update Packages", "Check Docker Status"). They can run a snippet with one click in any open terminal. They can also broadcast a snippet to multiple open terminals (tabs/panels) simultaneously.

**Why this priority**: P3 - Productivity enhancement, non-critical for MVP. Terminal already supports manual command entry.

**Independent Test**: Can be tested independently by verifying: User creates snippet → Executes snippet in terminal → Output appears → Runs snippet on multiple sessions. Does not require file manager or monitoring.

**Acceptance Scenarios**:

1. **Given** user has created a snippet "docker ps", **When** they open a terminal and click the snippet, **Then** command is sent and output appears
2. **Given** user has 3 terminal panels open, **When** they broadcast a snippet to all, **Then** command executes in all 3 panels; output streams independently

---

### Edge Cases

- What happens if an SSH host is deleted while a user has an active terminal session? (Terminal should gracefully close with "host deleted" message)
- How does the system handle commands that hang or produce extremely large output (>100MB)? (Backpressure handling, output buffering limits)
- What happens if a user's session token expires during an active terminal session? (Graceful logout, user re-authenticates)
- How does RBAC handle a user losing permission to a host while their terminal is open? (Terminal closes, user sees permission denied)
- What happens if SFTP connection fails mid-file-transfer? (User sees error; partial transfers are not committed)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support user registration with email/password (bcrypt hashing) and local authentication
- **FR-002**: System MUST support SSO via OpenID Connect (OIDC) with providers: Google, Okta, Keycloak (configurable)
- **FR-003**: System MUST support optional 2FA via TOTP (Google Authenticator compatible)
- **FR-004**: System MUST support RBAC with customizable roles (Admin, User, ReadOnly, custom) and permissions (host view, host connect, file upload, user manage, etc.)
- **FR-005**: Users MUST be able to register SSH hosts with: hostname, IP, port, authentication (password or private key), tags, folders
- **FR-006**: SSH host credentials (passwords, private keys) MUST be encrypted at-rest using application-level encryption (cryptography library)
- **FR-007**: Users MUST be able to open interactive SSH terminal sessions via WebSocket with full PTY support (stdin/stdout/stderr streaming)
- **FR-008**: Terminal MUST support multiple sessions via tabs, and multiple panes (max 4) per tab
- **FR-009**: Terminal MUST support customizable themes (Dracula, Solarized, etc.) and font settings, persisted per user
- **FR-010**: Terminal MUST handle WebSocket reconnection: client timeout 60s, server cleanup after 5 min inactivity, session state persists across brief reconnections
- **FR-011**: Backend MUST stream real-time server stats (CPU, memory, disk, network, uptime, OS info) via WebSocket every 5 seconds
- **FR-012**: Users MUST be able to upload/download files via SFTP with drag-and-drop support
- **FR-013**: Users MUST be able to edit text/code files inline using Monaco editor with save functionality
- **FR-014**: Users MUST be able to preview media files (images, audio, video) directly in browser
- **FR-015**: Users MUST be able to manage file permissions (chmod) via file manager UI
- **FR-016**: Users MUST be able to create and manage SSH port forwards (local and remote)
- **FR-017**: SSH tunnels MUST auto-reconnect if connection drops
- **FR-018**: Users MUST be able to create and execute command snippets in terminal(s)
- **FR-019**: Administrators MUST be able to view and terminate active user sessions
- **FR-020**: System MUST support multi-tenancy: users can only access hosts and sessions assigned to their roles
- **FR-021**: All sensitive data (credentials, private keys, tokens) MUST be encrypted at-rest and transmitted over HTTPS/TLS 1.3
- **FR-022**: System MUST enforce rate limiting on login endpoints (max 5 failures/min per IP)
- **FR-023**: System MUST support data export/import (SSH hosts, credentials, snippets) in JSON/CSV format
- **FR-024**: UI MUST support multi-language: English and Korean (i18next-based)
- **FR-025**: UI MUST support responsive design (desktop-first) with mobile support for host listing and stats viewing
- **FR-026**: UI MUST support dark mode / light mode toggle, persisted per user
- **FR-027**: HTTPS/SSL MUST be automatically provisioned via Let's Encrypt and Nginx; auto-renewal configured
- **FR-028**: All authentication events, session changes, and SFTP operations MUST be logged to centralized logging (JSON format)
- **FR-029**: Audit logs MUST include: timestamp, user, session_id, action, result, IP address, user agent (retained ≥90 days)
- **FR-030**: System MUST prevent sensitive data in logs: no passwords, SSH keys, or token contents

### Key Entities *(include if feature involves data)*

- **User**: username, email, password_hash, oidc_provider_id, 2fa_secret, roles, permissions, created_at, last_login
- **SSHHost**: id, name, hostname, ip_address, port, auth_type (password/key), encrypted_credentials, tags, folder_path, owner_user_id, created_at, updated_at
- **SSHSession**: id, user_id, host_id, session_token, started_at, last_activity, status (active/closed), connection_type (terminal/stats/tunnel)
- **AuditLog**: id, user_id, session_id, action, timestamp, result, ip_address, user_agent
- **CommandSnippet**: id, user_id, name, command_text, created_at
- **SSHTunnel**: id, user_id, host_id, tunnel_type (local/remote), local_port, remote_address, remote_port, status, created_at

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete login (SSO or password) in under 2 seconds
- **SC-002**: Terminal session opens and responds to first keystroke within 2 seconds of clicking "Open Terminal"
- **SC-003**: Terminal commands receive output with ≤100ms latency (p95 measured)
- **SC-004**: Real-time stats update every 5 seconds with zero data loss across ≥10 hosts simultaneously
- **SC-005**: File uploads complete at ≥5 MB/s on local network (SFTP baseline)
- **SC-006**: File downloads complete at ≥5 MB/s on local network (SFTP baseline)
- **SC-007**: Dashboard loads within 2 seconds on modern browsers (Chrome, Firefox, Safari)
- **SC-008**: System supports ≥100 concurrent users with ≤2s response time for API requests (p95)
- **SC-009**: System supports ≥10 concurrent terminal sessions per user without performance degradation
- **SC-010**: Audit logs capture 100% of authentication attempts, session events, and SFTP operations
- **SC-011**: Failed login lock-out activates after 5 failures/min per IP; user cannot retry until lockout expires (15 min default)
- **SC-012**: Privilege escalation attempts (e.g., user tries to access admin-only host) are blocked and logged
- **SC-013**: Session tokens expire after 1 hour (configurable) and force re-authentication
- **SC-014**: WebSocket reconnection succeeds for network interruptions ≤30 seconds; longer interruptions require re-login
- **SC-015**: HTTPS certificate auto-renewal succeeds for ≥95% of attempts; failures trigger admin alerts
- **SC-016**: Mobile UI correctly displays host list and stats on screens ≥320px wide (iPhone SE+ and larger)
- **SC-017**: Terminal emulation (xterm.js) supports ≥99% of ANSI escape sequences for common Linux shells
- **SC-018**: 95% of users successfully complete login + open terminal + execute a command on first attempt without support
- **SC-019**: Data export completes in ≤5 seconds for ≤1000 hosts; import validates and completes in ≤10 seconds

### Non-Functional Requirements

- **NFR-001**: All communication between client and backend MUST use HTTPS/TLS 1.3+
- **NFR-002**: Session secrets MUST use cryptographically secure random (CSPRNG)
- **NFR-003**: CORS policy MUST explicitly whitelist frontend origin (no wildcard)
- **NFR-004**: Database connections MUST use encryption at-rest where applicable
- **NFR-005**: OWASP Top 10 vulnerabilities MUST be tested and remediated before release
- **NFR-006**: Code MUST pass linting and type-checking (TypeScript for frontend, Python type hints for backend)
- **NFR-007**: All new features MUST have test coverage ≥80% for security-critical paths (auth, SFTP, terminal I/O)
- **NFR-008**: Performance regression testing MUST run on every commit; API p95 latency MUST not increase >10%
- **NFR-009**: System MUST gracefully handle SSH connection failures and display user-friendly error messages
- **NFR-010**: Large file transfers (>100MB) MUST implement backpressure handling to prevent memory leaks

## Assumptions

This specification makes the following assumptions for areas not explicitly detailed:

1. **Database Choice**: PostgreSQL is used for persistent storage (as per architecture description). If a different database is required, this must be explicitly specified.

2. **SSH Library**: Backend uses `asyncssh` for Python (per architecture). If a different SSH library is used, compatibility must be verified.

3. **Terminal Emulator**: Frontend uses `xterm.js` for terminal UI. If a different terminal library is required, feature parity must be ensured.

4. **Authentication Framework**: OIDC integration uses standard Python libraries (e.g., `python-jose`, `fastapi-security`). Custom implementations must maintain security standards.

5. **Encryption**: Application-level encryption uses `cryptography` library with AES-256-GCM for credentials. Key management and rotation procedures are TBD.

6. **Deployment**: Docker Compose is the primary deployment mechanism (per architecture). Kubernetes or other orchestration frameworks may be added in future versions.

7. **Mobile Support**: Mobile UI supports viewing and basic host listing/stats; full terminal access optimized for desktop. Mobile terminal access may be limited due to screen size.

8. **Data Retention**: Audit logs retained for ≥90 days (configurable per compliance requirements). Default retention policy uses PostgreSQL + external logging service.

9. **Rate Limiting**: Implemented at API level (FastAPI middleware). Load balancer-level rate limiting may be added for production deployments.

10. **Session Management**: JWT tokens used for stateless session management. Token refresh and expiration policies follow industry standards.

---

## Implementation Decisions

The following clarifications were resolved on 2025-11-08:

### Decision 1: Key Encryption Strategy

**Chosen**: **Option A - Single Master Key** stored in environment variable per deployment

**Rationale**:
- Simple initial implementation suitable for MVP
- All credentials encrypted with same master key (symmetric AES-256-GCM)
- Key stored in `ENCRYPTION_MASTER_KEY` environment variable
- Key rotation requires manual intervention and redeployment
- Suitable for single-deployment, enterprise scenarios; upgrade path to Vault available

**Implementation Notes**:
- Master key must be ≥32 bytes (256-bit)
- Key should be generated securely and stored in deployment secrets manager
- Future upgrades can migrate to per-user keys or external vault without breaking the API contract

---

### Decision 2: OIDC Provider Configuration

**Chosen**: **Option B - Admin UI with Manual Restart**

**Rationale**:
- Provides administrator flexibility without adding infrastructure dependencies
- Admins can configure OIDC providers via web UI (admin dashboard)
- Configuration changes stored in PostgreSQL
- Changes take effect after service restart (configurable via admin UI with confirmation)
- Suitable for scenarios where SSO provider changes are infrequent
- Path to dynamic configuration (Option C) available for future iterations

**Implementation Notes**:
- Admin UI includes "SSO Providers" settings page
- Providers include: name, client_id, client_secret, discovery_url, enabled flag
- Provider configuration changes trigger a "Configuration Changed" alert requiring restart
- Restart can be manual (admin-initiated) or scheduled (off-hours)
- Future: Implement Option C (dynamic reload) when stability requirements permit

---

*Specification created on 2025-11-08. Clarifications resolved on 2025-11-08. Based on comprehensive project description with 6 major feature areas (Host Manager, Terminal, Server Stats, File Manager, Tunnels, Tools) and infrastructure requirements.*
