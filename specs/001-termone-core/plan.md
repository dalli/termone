# Implementation Plan: Termone - Web-Based SSH Infrastructure Management Platform

**Branch**: `001-termone-core` | **Date**: 2025-11-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification for complete SSH infrastructure management platform

**Note**: This plan is filled in by the `/speckit.plan` command. Phases: 0 (Research) → 1 (Design) → 2 (Tasks generation via `/speckit.tasks`).

## Summary

Termone is a Docker Compose-deployed, all-in-one server and infrastructure management solution providing web-based SSH terminal, SSH tunneling, SFTP file management, real-time server monitoring, and command snippet management with SSO authentication and RBAC. The platform uses FastAPI (Python) backend with React/TypeScript frontend, PostgreSQL database, and WebSocket for real-time features.

**Core user flows**:
1. Admin/User logs in via SSO/local auth → Dashboard
2. Registers SSH hosts with encrypted credentials → Organizes by tags/folders
3. Opens interactive SSH terminal → Multi-session/multi-pane support
4. Views real-time server stats (CPU, memory, disk, network) via WebSocket
5. Manages remote files via SFTP with inline editing
6. Creates and executes command snippets across multiple terminals
7. Configures port tunnels (local/remote) with auto-reconnection

## Technical Context

**Language/Version**:
- Backend: Python 3.11+ (FastAPI async framework)
- Frontend: Node.js 18+ (React 18+ with TypeScript 5+)
- Target: Modern browsers (Chrome, Firefox, Safari, Edge)

**Primary Dependencies**:
- Backend: FastAPI, asyncssh, python-jose, pydantic, sqlalchemy, psycopg2-async
- Frontend: React, TypeScript, Vite, Tailwind CSS, Shadcn/ui, xterm.js, monaco-editor, react-router
- DevOps: Docker, Docker Compose, Nginx, Certbot (Let's Encrypt)

**Storage**: PostgreSQL 14+ (relational DB for users, hosts, sessions, audit logs, credentials)

**Testing**:
- Backend: pytest, pytest-asyncio, FastAPI TestClient, unittest.mock
- Frontend: Vitest, React Testing Library, Playwright (E2E)

**Target Platform**: Linux/Docker (primary), with HTTPS/TLS 1.3 everywhere

**Project Type**: Web application with frontend/backend separation (MPA-style with multiple entry points)

**Performance Goals**:
- Terminal responsiveness: ≤100ms latency (p95) command-to-output
- API responses: ≤500ms (p95) for most endpoints
- Real-time stats: 5-second update interval via WebSocket
- File transfers: ≥5 MB/s throughput on local networks
- Dashboard: ≤2s page load time
- Concurrent support: ≥100 simultaneous users, ≥10 concurrent terminal sessions per user

**Constraints**:
- No hardcoded secrets (all via environment variables)
- No SSH keys stored server-side (client provides or vault retrieves)
- Session tokens expire every 1 hour (configurable)
- WebSocket reconnection timeout: 30 seconds
- Large output handling: backpressure at 100KB chunks
- CORS: Explicit whitelist (no wildcards)

**Scale/Scope**:
- Estimated 6 major features (Host Manager, Terminal, Stats, File Manager, Tunnels, Snippets)
- ~30 API endpoints (estimated from 30 functional requirements)
- ~50-60 React components across 5-6 major pages
- Single deployment (monolithic Docker image per service)
- MVP: 100-500 users; enterprise scale: 5,000+ users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle Compliance Verification

**I. Security First (Non-Negotiable)** ✅ PASS
- Every SSH/SFTP session requires SSO authentication (FR-001, FR-002, FR-003 mandate local + OIDC + 2FA)
- All network traffic encrypted TLS 1.3+ (FR-021, NFR-002, NFR-003 require HTTPS everywhere)
- SSH keys never logged (FR-030, NFR-7 audit logging excludes credentials)
- Session tokens expire every 1 hour (SC-013)
- Privilege escalation logged (SC-012, FR-029 audit events)
- OWASP Top 10 testing required (NFR-005)

**II. API-First Architecture** ✅ PASS
- OpenAPI/Swagger specification required for all endpoints (implementation decision: create in Phase 1)
- Consistent error responses (NFR-7: standard error format with codes across all endpoints)
- All state changes flow through API (Web terminal, file ops, tunnels via WebSocket/REST)
- Frontend/backend separation enforced (MPA architecture with Nginx proxy)

**III. Test-First for Security-Critical Paths** ✅ PASS
- Authentication/authorization tests (FR-001-004, contract tests for auth endpoints)
- SSH session handling tests (FR-007-010, integration tests for PTY lifecycle)
- SFTP operation tests (FR-012-015, file transfer integrity tests)
- Permission boundary tests (FR-020, SC-012, privilege escalation prevention)
- Target coverage: ≥80% for security paths (NFR-007)

**IV. Integration Testing** ✅ PASS
- SSO integration: OIDC provider → session creation → backend verification (FR-002, FR-028)
- SSH tunnel lifecycle: Create → Authenticate → Command stream → Close (FR-016-017)
- SFTP workflow: List → Download/Upload → Permissions → Handle errors (FR-012-015)
- Permission boundaries: User/host/permission isolation (FR-020, SC-012)
- Concurrent operations (FR-008, FR-018, multi-session support)

**V. Observability & Audit Logging** ✅ PASS
- Structured JSON logging (FR-028 requirement)
- Comprehensive event capture (FR-029: auth events, session changes, SFTP ops)
- 90-day audit retention (FR-029)
- No sensitive data in logs (FR-030: no passwords, keys, tokens)

**VI. Real-time Communication with Resilience** ✅ PASS
- WebSocket streaming with heartbeat (FR-007, FR-011: 5s stats, terminal real-time)
- Heartbeat pings every 30s (FR-010 specification)
- Reconnection handling: <30s restores session, >30s requires re-auth (SC-014)
- Large output backpressure (NFR-010: >100KB streamed with flow control)
- Graceful shutdown (browser tab close → WebSocket close → SSH session cleanup)

### Gate Result
**✅ GATES PASS** - Specification fully aligns with all 6 Termone constitutional principles. No violations or exceptions required.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── auth.py              # Login, logout, 2FA, OIDC endpoints
│   │   ├── hosts.py             # SSH host CRUD, search, bulk operations
│   │   ├── terminal.py          # WebSocket: PTY streams, session mgmt
│   │   ├── stats.py             # WebSocket: Real-time server stats
│   │   ├── files.py             # SFTP operations: upload, download, edit
│   │   ├── tunnels.py           # SSH tunnel CRUD, status, reconnection
│   │   ├── snippets.py          # Command snippet CRUD, execution
│   │   ├── admin.py             # User/session management (admin-only)
│   │   └── health.py            # Health checks, metrics
│   ├── models/
│   │   ├── user.py              # User, Role, Permission models
│   │   ├── ssh_host.py          # SSHHost, Credential models
│   │   ├── session.py           # SSHSession, TerminalSession models
│   │   ├── audit_log.py         # AuditLog model (structured events)
│   │   └── snippet.py           # CommandSnippet model
│   ├── services/
│   │   ├── auth.py              # JWT, OIDC, 2FA logic
│   │   ├── ssh_client.py        # asyncssh wrapper, connection pooling
│   │   ├── encryption.py        # Credential encryption/decryption
│   │   ├── stats_collector.py   # Periodic stats collection via SSH
│   │   ├── audit.py             # Structured logging to DB/external
│   │   └── tunnel.py            # SSH tunnel management, auto-reconnect
│   ├── middleware/
│   │   ├── auth.py              # JWT token validation
│   │   ├── rate_limit.py        # Rate limiting (login endpoints)
│   │   └── cors.py              # CORS policy enforcement
│   ├── database/
│   │   ├── __init__.py
│   │   ├── migrations/          # Alembic migrations for schema
│   │   └── seeders.py           # Test data seeding (development only)
│   ├── config.py                # Environment-based config (FastAPI settings)
│   └── main.py                  # FastAPI app initialization, startup/shutdown
├── tests/
│   ├── contract/
│   │   ├── test_auth.py         # Auth endpoint contracts
│   │   ├── test_hosts.py        # Host CRUD contracts
│   │   ├── test_terminal.py     # WebSocket protocol contracts
│   │   └── test_files.py        # SFTP operation contracts
│   ├── integration/
│   │   ├── test_auth_flow.py    # SSO → session → DB verification
│   │   ├── test_ssh_tunnel.py   # SSH tunnel lifecycle
│   │   ├── test_sftp_workflow.py  # File operations end-to-end
│   │   └── test_permissions.py  # Permission boundary enforcement
│   └── unit/
│       ├── test_encryption.py   # Credential encryption
│       ├── test_models.py       # Model validation
│       └── test_services.py     # Service business logic
├── requirements.txt             # Python dependencies (pip)
├── Dockerfile                   # Backend image
└── alembic.ini                  # Database migrations config

frontend/
├── src/
│   ├── pages/
│   │   ├── auth.tsx             # Login/SSO/2FA pages (entry point 1)
│   │   ├── dashboard.tsx        # Dashboard page (entry point 2)
│   │   ├── hosts.tsx            # Host manager page (entry point 3)
│   │   ├── terminal.tsx         # Terminal/SSH page (entry point 4)
│   │   ├── files.tsx            # File manager page (entry point 5)
│   │   ├── stats.tsx            # Stats/monitoring page (entry point 6)
│   │   ├── admin.tsx            # Admin panel (entry point 7)
│   │   └── NotFound.tsx
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── OIDCSelector.tsx
│   │   │   └── TwoFactorSetup.tsx
│   │   ├── hosts/
│   │   │   ├── HostList.tsx
│   │   │   ├── HostForm.tsx
│   │   │   ├── HostSearch.tsx
│   │   │   └── KeyDeploymentModal.tsx
│   │   ├── terminal/
│   │   │   ├── XTerminal.tsx
│   │   │   ├── TerminalTabs.tsx
│   │   │   ├── TerminalPanel.tsx
│   │   │   └── ThemeSelector.tsx
│   │   ├── files/
│   │   │   ├── FileExplorer.tsx
│   │   │   ├── FileUpload.tsx
│   │   │   ├── FileEditor.tsx
│   │   │   └── MediaViewer.tsx
│   │   ├── stats/
│   │   │   ├── CPUChart.tsx
│   │   │   ├── MemoryChart.tsx
│   │   │   ├── DiskChart.tsx
│   │   │   └── SystemInfo.tsx
│   │   ├── tunnels/
│   │   │   ├── TunnelList.tsx
│   │   │   ├── TunnelForm.tsx
│   │   │   └── TunnelStatus.tsx
│   │   ├── snippets/
│   │   │   ├── SnippetLibrary.tsx
│   │   │   ├── SnippetForm.tsx
│   │   │   └── SnippetExecutor.tsx
│   │   ├── common/
│   │   │   ├── Navbar.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Loading.tsx
│   │   │   └── ErrorBoundary.tsx
│   │   └── ui/
│   │       └── (Shadcn/ui components: Button, Input, Dialog, etc.)
│   ├── services/
│   │   ├── api.ts               # HTTP client (axios/fetch wrapper)
│   │   ├── websocket.ts         # WebSocket manager (terminal, stats)
│   │   ├── auth.ts              # Auth helper (JWT storage/retrieval)
│   │   └── storage.ts           # LocalStorage manager (theme, preferences)
│   ├── hooks/
│   │   ├── useAuth.ts           # Auth state management
│   │   ├── useTerminal.ts       # Terminal WebSocket management
│   │   ├── useStats.ts          # Stats WebSocket management
│   │   └── usePagination.ts     # Common pagination logic
│   ├── context/
│   │   ├── AuthContext.tsx      # User, roles, permissions
│   │   └── ThemeContext.tsx     # Dark/light mode
│   ├── types/
│   │   ├── api.ts               # API request/response types
│   │   ├── models.ts            # Backend model types
│   │   └── websocket.ts         # WebSocket message types
│   ├── i18n/
│   │   ├── en.json              # English translations
│   │   ├── ko.json              # Korean translations
│   │   └── i18n.ts              # i18next configuration
│   ├── styles/
│   │   └── globals.css          # Global Tailwind styles
│   ├── utils/
│   │   ├── format.ts            # Date, size, number formatting
│   │   ├── validation.ts        # Form validation helpers
│   │   └── error.ts             # Error message helpers
│   └── main.tsx                 # Root entry point (common assets)
├── public/
│   ├── index.html               # Base HTML template
│   ├── auth.html                # Auth page entry
│   ├── dashboard.html           # Dashboard page entry
│   ├── hosts.html               # Hosts page entry
│   ├── terminal.html            # Terminal page entry
│   ├── files.html               # Files page entry
│   ├── stats.html               # Stats page entry
│   └── admin.html               # Admin page entry
├── tests/
│   ├── unit/
│   │   ├── services.test.ts
│   │   ├── hooks.test.ts
│   │   └── utils.test.ts
│   ├── integration/
│   │   ├── auth.test.ts
│   │   ├── terminal.test.ts
│   │   └── files.test.ts
│   └── e2e/
│       ├── auth.spec.ts         # Playwright auth flow
│       ├── terminal.spec.ts     # Playwright terminal tests
│       └── files.spec.ts        # Playwright file manager tests
├── package.json                 # Node dependencies
├── tsconfig.json                # TypeScript config
├── vite.config.ts               # Vite bundler config (multiple entries)
├── vitest.config.ts             # Unit test config
├── .env.example                 # Environment variable template
└── Dockerfile                   # Frontend image

docker-compose.yml              # Orchestration (frontend, backend, postgres, nginx)
nginx/
├── Dockerfile                   # Nginx reverse proxy image
├── nginx.conf                   # Proxy config, SSL setup
└── certbot.conf                 # Let's Encrypt certificate renewal

.github/
├── workflows/
│   ├── ci.yml                   # Tests on every push
│   ├── security-scan.yml        # Dependency scanning
│   └── build-deploy.yml         # Build & push Docker images
└── dependabot.yml               # Automated dependency updates

.env.example                     # Top-level env template
.gitignore
README.md                        # Project overview
CONTRIBUTING.md                 # Development guide
CHANGELOG.md                     # Release notes
```

**Structure Decision**:
- **Selected: Option 2 - Web Application** with frontend/backend separation
- **Rationale**:
  - Frontend: MPA-style with Vite for multiple page entry points (faster initial load than SPA)
  - Backend: FastAPI async Python for efficient concurrent terminal/stats streaming
  - Separation: Enables parallel frontend/backend development, independent scaling, clear API contracts
  - DevOps: Single Docker Compose deployment with Nginx reverse proxy, automatic SSL via Certbot

## Complexity Tracking

No violations identified. All constitutional gates pass. No complexity justifications required.

---

## Phase 0: Research & Unknowns

**Status**: ✅ COMPLETE

All technical unknowns resolved from spec and implementation decisions:

1. **Encryption Strategy**: Option A - Single Master Key (AES-256-GCM via `ENCRYPTION_MASTER_KEY` env var)
2. **OIDC Configuration**: Option B - Admin UI with manual restart
3. **Framework Choices**: FastAPI (Python 3.11+), React 18+ (TypeScript), PostgreSQL 14+
4. **Async SSH**: asyncssh library for non-blocking SSH/SFTP operations
5. **Real-time**: WebSocket via FastAPI's Starlette, reconnection logic on client
6. **Terminal Emulation**: xterm.js (industry standard)
7. **File Editing**: Monaco Editor (VS Code engine)
8. **API Contract**: OpenAPI 3.0 via FastAPI's auto-documentation (to be detailed in Phase 1)

**Research Summary**: No clarifications needed. Technical stack is well-defined and industry-standard. Moving to Phase 1.

---

## Phase 1: Design & Implementation Artifacts

**Status**: ✅ COMPLETE (2025-11-08)

All Phase 1 design artifacts generated successfully:
- ✅ research.md - Phase 0 research with all technology decisions documented
- ✅ data-model.md - PostgreSQL schema with 14 core tables and comprehensive entity relationships
- ✅ contracts/openapi.yaml - Complete OpenAPI 3.0 specification with all endpoints and request/response schemas
- ✅ quickstart.md - Development setup guide (Docker Compose and local development)
- ⏳ Agent context update - Pending (script execution)

**Completion Notes**:
- Research phase resolved all technical unknowns (encryption strategy, OIDC config, framework choices)
- Data model fully normalized with proper constraints, validations, and indexes
- API contracts fully specified with standard error handling and authentication
- Development quickstart covers Docker, local setup, testing procedures, and troubleshooting

**Next Phase**: Task generation via `/speckit.tasks` to break 6 user stories into implementation tasks
