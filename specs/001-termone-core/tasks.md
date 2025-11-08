# Tasks: Termone - Web-Based SSH Infrastructure Management Platform

**Input**: Design documents from `/specs/001-termone-core/`
**Status**: ✅ Ready for implementation
**Branch**: `001-termone-core`
**Last Updated**: 2025-11-08

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., [US1], [US2], [US3])
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, and environment configuration

- [ ] T001 Create project directory structure per plan.md (backend/src/, backend/tests/, frontend/src/, frontend/tests/, nginx/, .github/workflows/)
- [ ] T002 [P] Initialize backend Python environment: Python 3.11+, venv, requirements.txt with core deps (FastAPI, SQLAlchemy, asyncssh, cryptography, python-jose, passlib, pydantic)
- [ ] T003 [P] Initialize frontend Node.js environment: Node 18+, package.json with deps (React 18+, TypeScript, Vite, Tailwind, Shadcn/ui, xterm.js, monaco-editor, axios)
- [ ] T004 [P] Configure backend linting/formatting: flake8, black, isort, pre-commit hooks
- [ ] T005 [P] Configure frontend linting/formatting: ESLint, Prettier, TypeScript strict mode
- [ ] T006 Create .env.example with all required environment variables (ENCRYPTION_MASTER_KEY, JWT_SECRET, DATABASE_URL, OIDC_* vars, etc.)
- [ ] T007 Create docker-compose.yml with services: backend, frontend, postgres, nginx
- [ ] T008 Create backend/Dockerfile and frontend/Dockerfile with multi-stage builds
- [ ] T009 Create nginx/nginx.conf with reverse proxy configuration and SSL setup
- [ ] T010 Create GitHub Actions workflows: .github/workflows/ci.yml (tests), security-scan.yml (dependency check), build-deploy.yml

**Checkpoint**: Project structure and build configuration ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & Migrations

- [ ] T011 Create Alembic migration structure in backend/alembic/ with versions/ directory and env.py
- [ ] T012 Create database migration for User, Role, Permission, UserRole, RolePermission tables in backend/alembic/versions/001_create_users_roles.py
- [ ] T013 Create database migration for SSHHost, Credential, OIDCProvider tables in backend/alembic/versions/002_create_infrastructure.py
- [ ] T014 Create database migration for SSHSession, TerminalSession, AuditLog, CommandSnippet, SSHTunnel, RefreshToken tables in backend/alembic/versions/003_create_sessions_and_operations.py
- [ ] T015 Create database models in backend/src/models/:
  - [ ] T015a [P] backend/src/models/user.py (User, Role, Permission, UserRole, RolePermission, TOTPSecret, RefreshToken)
  - [ ] T015b [P] backend/src/models/infrastructure.py (SSHHost, Credential, OIDCProvider)
  - [ ] T015c [P] backend/src/models/session.py (SSHSession, TerminalSession)
  - [ ] T015d [P] backend/src/models/audit.py (AuditLog)
  - [ ] T015e [P] backend/src/models/snippet.py (CommandSnippet)
  - [ ] T015f [P] backend/src/models/tunnel.py (SSHTunnel)

### Authentication & Authorization

- [ ] T016 Implement encryption service in backend/src/services/encryption.py (AES-256-GCM with ENCRYPTION_MASTER_KEY)
- [ ] T017 Implement JWT service in backend/src/services/jwt_service.py (token generation, validation, refresh)
- [ ] T018 Implement OIDC discovery and provider loader in backend/src/services/oidc_service.py (reads OIDCProvider from DB)
- [ ] T019 Implement RBAC permission checker in backend/src/services/permission_service.py (check user permissions for host/operation)
- [ ] T020 Create authentication middleware in backend/src/middleware/auth.py (JWT validation, session extraction)
- [ ] T021 Create error handling middleware in backend/src/middleware/errors.py (standard error responses with error codes)
- [ ] T022 Create audit logging middleware in backend/src/middleware/audit.py (log all API requests/responses with user context)

### API Framework & Configuration

- [ ] T023 Create FastAPI app initialization in backend/src/main.py with:
  - [ ] CORS configuration (explicit whitelist)
  - [ ] Middleware stack (auth, error, audit, rate limiting)
  - [ ] Database session management
  - [ ] Health check endpoint
  - [ ] OpenAPI documentation configuration
- [ ] T024 Create database session factory in backend/src/database.py (SQLAlchemy async session management)
- [ ] T025 Create configuration management in backend/src/config.py (environment variable parsing, validation)
- [ ] T026 Create base exception classes in backend/src/exceptions.py (AuthException, PermissionException, ValidationException, etc.)
- [ ] T027 Create standard response models in backend/src/schemas/common.py (ErrorResponse, SuccessResponse with typed payloads)

### Real-time Infrastructure

- [ ] T028 Create WebSocket manager in backend/src/services/websocket_manager.py (connection tracking, broadcast, cleanup)
- [ ] T029 Create connection pool for concurrent SSH sessions in backend/src/services/ssh_pool.py (session caching, cleanup)
- [ ] T030 Create rate limiting service in backend/src/services/rate_limiter.py (per-IP login attempt tracking)

### Frontend Setup

- [ ] T031 Create Vite configuration in frontend/vite.config.ts with MPA setup (7 entry points: auth, dashboard, hosts, terminal, files, stats, admin)
- [ ] T032 Create TypeScript configuration in frontend/tsconfig.json with strict mode
- [ ] T033 Create global styles in frontend/src/styles/globals.css (Tailwind base, responsive utilities)
- [ ] T034 Create API client in frontend/src/services/api.ts (axios wrapper, JWT token handling, error interceptors)
- [ ] T035 Create WebSocket client in frontend/src/services/websocket.ts (connection management, reconnection logic, message routing)
- [ ] T036 Create authentication context in frontend/src/context/AuthContext.tsx (user state, roles, permissions, token management)
- [ ] T037 Create theme context in frontend/src/context/ThemeContext.tsx (dark/light mode with localStorage persistence)
- [ ] T038 Create i18n setup in frontend/src/i18n/i18n.ts with en/ko language files
- [ ] T039 Create base layout component in frontend/src/components/common/Layout.tsx (navbar, sidebar, main content area)
- [ ] T040 Create error boundary component in frontend/src/components/common/ErrorBoundary.tsx

### Testing Infrastructure (Contract Tests for Auth - Foundation)

- [ ] T041 [P] Create contract test suite structure in backend/tests/contract/
- [ ] T042 [P] Create integration test suite structure in backend/tests/integration/
- [ ] T043 [P] Create frontend test setup with Vitest and React Testing Library in frontend/vitest.config.ts
- [ ] T044 [P] Create Playwright configuration in frontend/playwright.config.ts for E2E tests
- [ ] T045 Create pytest fixtures in backend/tests/conftest.py (database fixtures, FastAPI test client, mock OIDC provider)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Admin Dashboard and Host Management (Priority: P1) 🎯 MVP

**Goal**: Users can register SSH hosts with credentials, organize them by tags/folders, search efficiently, and see host status on a dashboard

**Independent Test**: Can be tested by verifying: Admin login → Register host (password) → Register host (SSH key) → Search/filter hosts → Dashboard displays data → Independent of terminal/file features

### Contract Tests for User Story 1

- [ ] T046 [P] [US1] Contract test for POST /auth/login in backend/tests/contract/test_auth.py (verify JWT token returned)
- [ ] T047 [P] [US1] Contract test for POST /hosts in backend/tests/contract/test_hosts.py (verify host creation with encrypted credentials)
- [ ] T048 [P] [US1] Contract test for GET /hosts in backend/tests/contract/test_hosts.py (verify list with pagination, filtering)
- [ ] T049 [P] [US1] Contract test for GET /hosts/{host_id} in backend/tests/contract/test_hosts.py
- [ ] T050 [P] [US1] Contract test for PUT /hosts/{host_id} in backend/tests/contract/test_hosts.py
- [ ] T051 [P] [US1] Contract test for DELETE /hosts/{host_id} in backend/tests/contract/test_hosts.py
- [ ] T052 [P] [US1] Contract test for POST /hosts/{host_id}/deploy-public-key in backend/tests/contract/test_hosts.py

### Backend Implementation for User Story 1

- [ ] T053 [P] [US1] Implement HostService in backend/src/services/host_service.py (CRUD, search, filtering, bulk operations)
- [ ] T054 [P] [US1] Implement CredentialService in backend/src/services/credential_service.py (encryption/decryption of passwords and keys)
- [ ] T055 [US1] Implement host API endpoints in backend/src/api/hosts.py:
  - POST /hosts (create with encrypted credentials)
  - GET /hosts (list with pagination, tags, folder filtering)
  - GET /hosts/{host_id}
  - PUT /hosts/{host_id}
  - DELETE /hosts/{host_id}
  - POST /hosts/{host_id}/deploy-public-key (batch deploy SSH keys)
  - GET /hosts/search (full-text search)
- [ ] T056 [P] [US1] Create Pydantic schemas in backend/src/schemas/hosts.py (HostCreate, HostUpdate, HostResponse, CredentialCreate, etc.)
- [ ] T057 [US1] Implement permission checks in host endpoints (verify user can access host per RBAC)
- [ ] T058 [US1] Implement audit logging for host operations in backend/src/services/audit_service.py

### Frontend Implementation for User Story 1

- [ ] T059 [P] [US1] Create HostList component in frontend/src/components/hosts/HostList.tsx (display registered hosts with tags/folders)
- [ ] T060 [P] [US1] Create HostForm component in frontend/src/components/hosts/HostForm.tsx (create/edit hosts with credential input)
- [ ] T061 [P] [US1] Create HostSearch component in frontend/src/components/hosts/HostSearch.tsx (search and filter by hostname/tag)
- [ ] T062 [P] [US1] Create Dashboard component in frontend/src/components/common/Dashboard.tsx (host summary, recent hosts, quick stats)
- [ ] T063 [US1] Create hosts page in frontend/src/pages/hosts.tsx (HostList + HostForm integration)
- [ ] T064 [US1] Create dashboard page in frontend/src/pages/dashboard.tsx
- [ ] T065 [P] [US1] Create useHosts hook in frontend/src/hooks/useHosts.ts (manage host list state, API calls)
- [ ] T066 [P] [US1] Create useAuth hook in frontend/src/hooks/useAuth.ts (manage authentication state)
- [ ] T067 [US1] Create auth service in frontend/src/services/auth.ts (login, logout, token management)
- [ ] T068 [US1] Create HTML entry points: frontend/public/auth.html, frontend/public/dashboard.html, frontend/public/hosts.html

### Integration Tests for User Story 1

- [ ] T069 [US1] Integration test for admin login flow in backend/tests/integration/test_auth_flow.py
- [ ] T070 [US1] Integration test for host registration and retrieval in backend/tests/integration/test_host_lifecycle.py
- [ ] T071 [US1] Integration test for permission boundaries (user cannot access other user's hosts) in backend/tests/integration/test_permissions.py

**Checkpoint**: User Story 1 (Host Management) is fully functional and independently testable

---

## Phase 4: User Story 2 - SSH Terminal Access (Priority: P1)

**Goal**: Users connect to SSH hosts and interact with interactive PTY shell, with multi-session/multi-pane support and resilient WebSocket connections

**Independent Test**: Can be tested by verifying: User selects host → Opens terminal → Executes commands → Receives output → Multiple sessions work independently

### Contract Tests for User Story 2

- [ ] T072 [P] [US2] Contract test for WebSocket /ws/terminal/{session_id} in backend/tests/contract/test_terminal.py (verify connection, data streaming)
- [ ] T072a [P] [US2] Contract test for POST /terminal/sessions/{host_id} in backend/tests/contract/test_terminal.py (verify session creation returns session_id)
- [ ] T072b [P] [US2] Contract test for GET /terminal/sessions in backend/tests/contract/test_terminal.py (verify session list)
- [ ] T072c [P] [US2] Contract test for DELETE /terminal/sessions/{session_id} in backend/tests/contract/test_terminal.py (verify session cleanup)

### Backend Implementation for User Story 2

- [ ] T073 [P] [US2] Implement SSHClient wrapper in backend/src/services/ssh_client.py (async SSH connection, command execution, PTY spawning)
- [ ] T074 [P] [US2] Implement TerminalSessionService in backend/src/services/terminal_service.py (session lifecycle, PTY management)
- [ ] T075 [US2] Implement terminal session endpoints in backend/src/api/terminal.py:
  - POST /terminal/sessions/{host_id} (create session, return session_id)
  - GET /terminal/sessions (list active sessions)
  - DELETE /terminal/sessions/{session_id} (close session)
  - WebSocket /ws/terminal/{session_id} (PTY I/O streaming)
- [ ] T076 [P] [US2] Create schemas in backend/src/schemas/terminal.py (TerminalSessionCreate, TerminalSessionResponse, TerminalMessage)
- [ ] T077 [US2] Implement WebSocket handler for terminal in backend/src/api/terminal.py:
  - Accept WebSocket connection
  - Stream PTY output to client (non-blocking asyncio)
  - Receive client input and send to PTY (stdin)
  - Handle disconnection and cleanup
  - Implement heartbeat pings every 30s
  - Implement reconnection logic (session persists <30s)
- [ ] T078 [US2] Implement session timeout cleanup (5 min inactivity) in backend/src/services/background_tasks.py
- [ ] T079 [US2] Implement backpressure handling for large output (>100KB buffering) in WebSocket handler
- [ ] T080 [US2] Add terminal operation audit logging in backend/src/services/audit_service.py (session created, closed, commands executed)

### Frontend Implementation for User Story 2

- [ ] T081 [P] [US2] Create XTerminal component in frontend/src/components/terminal/XTerminal.tsx (integrate xterm.js library, input/output handling)
- [ ] T082 [P] [US2] Create TerminalTabs component in frontend/src/components/terminal/TerminalTabs.tsx (manage multiple terminal tabs)
- [ ] T083 [P] [US2] Create TerminalPanel component in frontend/src/components/terminal/TerminalPanel.tsx (handle 4-panel layout)
- [ ] T084 [P] [US2] Create ThemeSelector component in frontend/src/components/terminal/ThemeSelector.tsx (Dracula, Solarized, etc.)
- [ ] T085 [US2] Create terminal page in frontend/src/pages/terminal.tsx (integrate tabs, panels, theme selector)
- [ ] T086 [P] [US2] Create useTerminal hook in frontend/src/hooks/useTerminal.ts (manage WebSocket connection, session state)
- [ ] T087 [P] [US2] Create useWebSocket hook in frontend/src/hooks/useWebSocket.ts (generic WebSocket management with reconnection)
- [ ] T088 [US2] Create terminal service in frontend/src/services/terminal.ts (API calls for session management)
- [ ] T089 [US2] Implement theme persistence in localStorage (ThemeSelector updates context)
- [ ] T090 [US2] Implement session reconnection logic (detect disconnection, auto-reconnect <30s, preserve session state)
- [ ] T091 [US2] Create frontend/public/terminal.html entry point

### Integration Tests for User Story 2

- [ ] T092 [US2] Integration test for terminal session lifecycle in backend/tests/integration/test_terminal_lifecycle.py (create → connect → execute → close)
- [ ] T093 [US2] Integration test for WebSocket reconnection in backend/tests/integration/test_terminal_lifecycle.py (disconnect → auto-reconnect → session restored)
- [ ] T094 [US2] Integration test for large output handling in backend/tests/integration/test_terminal_backpressure.py (stream >100KB output)

**Checkpoint**: User Story 2 (Terminal) is fully functional and independently testable

---

## Phase 5: User Story 3 - Server Monitoring and Real-time Stats (Priority: P1)

**Goal**: Users see real-time CPU, memory, disk, network stats via WebSocket with 5-second updates and charts

**Independent Test**: Can be tested by verifying: User opens stats page → Data loads → Charts update every 5s → Data persists across refreshes

### Contract Tests for User Story 3

- [ ] T095 [P] [US3] Contract test for WebSocket /ws/stats/{host_id} in backend/tests/contract/test_stats.py (verify connection, data streaming every 5s)
- [ ] T095a [P] [US3] Contract test for GET /stats/{host_id}/current in backend/tests/contract/test_stats.py (verify current stats snapshot)

### Backend Implementation for User Story 3

- [ ] T096 [P] [US3] Implement StatsCollector in backend/src/services/stats_collector.py (periodically execute vmstat, free, df via SSH)
- [ ] T097 [P] [US3] Implement StatsService in backend/src/services/stats_service.py (aggregate stats, format for frontend)
- [ ] T098 [US3] Implement stats endpoints in backend/src/api/stats.py:
  - GET /stats/{host_id}/current (return current stats snapshot)
  - WebSocket /ws/stats/{host_id} (stream stats every 5s)
- [ ] T099 [P] [US3] Create schemas in backend/src/schemas/stats.py (CPUStats, MemoryStats, DiskStats, NetworkStats, SystemInfo, StatsMessage)
- [ ] T100 [US3] Implement WebSocket handler for stats in backend/src/api/stats.py:
  - Accept WebSocket connection
  - Start background task to collect stats every 5s
  - Stream stats to client
  - Handle multiple clients subscribed to same host (broadcast)
  - Cleanup on disconnection
- [ ] T101 [US3] Implement background stats collection in backend/src/services/background_tasks.py (asyncio task, per-host collection)
- [ ] T102 [US3] Add stats operation audit logging (stats collected, connection established/closed)

### Frontend Implementation for User Story 3

- [ ] T103 [P] [US3] Create CPUChart component in frontend/src/components/stats/CPUChart.tsx (chart.js or recharts)
- [ ] T104 [P] [US3] Create MemoryChart component in frontend/src/components/stats/MemoryChart.tsx
- [ ] T105 [P] [US3] Create DiskChart component in frontend/src/components/stats/DiskChart.tsx
- [ ] T106 [P] [US3] Create NetworkChart component in frontend/src/components/stats/NetworkChart.tsx
- [ ] T107 [P] [US3] Create SystemInfo component in frontend/src/components/stats/SystemInfo.tsx (OS, kernel, uptime display)
- [ ] T108 [US3] Create stats page in frontend/src/pages/stats.tsx (integrate all charts)
- [ ] T109 [P] [US3] Create useStats hook in frontend/src/hooks/useStats.ts (WebSocket connection, data aggregation)
- [ ] T110 [P] [US3] Create chart utilities in frontend/src/utils/charts.ts (format data for charts, aggregation)
- [ ] T111 [US3] Create frontend/public/stats.html entry point

### Integration Tests for User Story 3

- [ ] T112 [US3] Integration test for stats collection and streaming in backend/tests/integration/test_stats_lifecycle.py
- [ ] T113 [US3] Integration test for multiple clients receiving stats broadcasts in backend/tests/integration/test_stats_broadcast.py

**Checkpoint**: All P1 User Stories (1, 2, 3) are now complete and independently functional

---

## Phase 6: User Story 4 - Remote File Management via SFTP (Priority: P2)

**Goal**: Users navigate directories, upload/download files, edit text files inline, and manage permissions via SFTP

**Independent Test**: Can be tested by verifying: User navigates directory → Uploads file → Downloads file → Edits text file → Deletes file

### Contract Tests for User Story 4

- [ ] T114 [P] [US4] Contract test for GET /files/{host_id}/list in backend/tests/contract/test_files.py (verify directory listing)
- [ ] T115 [P] [US4] Contract test for POST /files/{host_id}/upload in backend/tests/contract/test_files.py (verify file upload)
- [ ] T116 [P] [US4] Contract test for GET /files/{host_id}/download in backend/tests/contract/test_files.py (verify file download)
- [ ] T117 [P] [US4] Contract test for POST /files/{host_id}/edit in backend/tests/contract/test_files.py (verify file read/write)
- [ ] T118 [P] [US4] Contract test for POST /files/{host_id}/chmod in backend/tests/contract/test_files.py (verify permission change)

### Backend Implementation for User Story 4

- [ ] T119 [P] [US4] Implement SFTPClient wrapper in backend/src/services/sftp_client.py (async SFTP operations)
- [ ] T120 [P] [US4] Implement FileService in backend/src/services/file_service.py (list, upload, download, edit, delete, chmod)
- [ ] T121 [US4] Implement file endpoints in backend/src/api/files.py:
  - GET /files/{host_id}/list (directory listing with metadata)
  - GET /files/{host_id}/download (file download with streaming)
  - POST /files/{host_id}/upload (multipart file upload)
  - POST /files/{host_id}/edit (read/write file content, sync to disk)
  - POST /files/{host_id}/delete (delete file/directory)
  - POST /files/{host_id}/chmod (change permissions)
  - POST /files/{host_id}/move (move/rename file)
- [ ] T122 [P] [US4] Create schemas in backend/src/schemas/files.py (DirectoryListing, FileInfo, UploadResponse, FileContent, ChmodRequest)
- [ ] T123 [US4] Implement permission checks for SFTP operations (verify user can upload/edit/delete per host permission)
- [ ] T124 [US4] Add file operation audit logging (upload, download, edit, delete, chmod)

### Frontend Implementation for User Story 4

- [ ] T125 [P] [US4] Create FileExplorer component in frontend/src/components/files/FileExplorer.tsx (directory tree, file list)
- [ ] T126 [P] [US4] Create FileUpload component in frontend/src/components/files/FileUpload.tsx (drag-drop, multipart upload)
- [ ] T127 [P] [US4] Create FileEditor component in frontend/src/components/files/FileEditor.tsx (Monaco editor integration)
- [ ] T128 [P] [US4] Create MediaViewer component in frontend/src/components/files/MediaViewer.tsx (image/audio/video preview)
- [ ] T129 [US4] Create files page in frontend/src/pages/files.tsx (FileExplorer + FileUpload + FileEditor)
- [ ] T130 [P] [US4] Create useFiles hook in frontend/src/hooks/useFiles.ts (file operations, state management)
- [ ] T131 [P] [US4] Create file utilities in frontend/src/utils/files.ts (file type detection, size formatting, mime type mapping)
- [ ] T132 [US4] Implement drag-drop file upload in FileUpload component
- [ ] T133 [US4] Create frontend/public/files.html entry point

### Integration Tests for User Story 4

- [ ] T134 [US4] Integration test for file upload and download in backend/tests/integration/test_file_lifecycle.py
- [ ] T135 [US4] Integration test for file editing in backend/tests/integration/test_file_edit.py
- [ ] T136 [US4] Integration test for permission boundary (user cannot access other user's files) in backend/tests/integration/test_file_permissions.py

**Checkpoint**: User Story 4 (File Manager) is fully functional

---

## Phase 7: User Story 5 - SSH Tunnel Management (Priority: P2)

**Goal**: Users create and manage SSH port forwarding (local/remote) with auto-reconnection

**Independent Test**: Can be tested by verifying: User creates tunnel → Tunnel appears in list → Can connect to forwarded port → Tunnel auto-reconnects on failure

### Contract Tests for User Story 5

- [ ] T137 [P] [US5] Contract test for POST /tunnels in backend/tests/contract/test_tunnels.py (verify tunnel creation)
- [ ] T138 [P] [US5] Contract test for GET /tunnels in backend/tests/contract/test_tunnels.py (verify tunnel list)
- [ ] T139 [P] [US5] Contract test for GET /tunnels/{tunnel_id}/status in backend/tests/contract/test_tunnels.py (verify status)
- [ ] T140 [P] [US5] Contract test for PUT /tunnels/{tunnel_id} in backend/tests/contract/test_tunnels.py (verify tunnel update)
- [ ] T141 [P] [US5] Contract test for DELETE /tunnels/{tunnel_id} in backend/tests/contract/test_tunnels.py (verify tunnel deletion)

### Backend Implementation for User Story 5

- [ ] T142 [P] [US5] Implement TunnelService in backend/src/services/tunnel_service.py (create, manage, reconnect SSH port forwards)
- [ ] T143 [P] [US5] Implement TunnelManager in backend/src/services/tunnel_manager.py (background task for tunnel lifecycle and reconnection)
- [ ] T144 [US5] Implement tunnel endpoints in backend/src/api/tunnels.py:
  - POST /tunnels (create tunnel with local/remote forward config)
  - GET /tunnels (list tunnels with status)
  - GET /tunnels/{tunnel_id}/status
  - PUT /tunnels/{tunnel_id} (update tunnel config)
  - DELETE /tunnels/{tunnel_id} (delete tunnel)
- [ ] T145 [P] [US5] Create schemas in backend/src/schemas/tunnels.py (TunnelCreate, TunnelUpdate, TunnelResponse, TunnelStatus)
- [ ] T146 [US5] Implement tunnel auto-reconnection in TunnelManager (detect connection loss, retry after 30s)
- [ ] T147 [US5] Add tunnel operation audit logging

### Frontend Implementation for User Story 5

- [ ] T148 [P] [US5] Create TunnelList component in frontend/src/components/tunnels/TunnelList.tsx (display active tunnels with status)
- [ ] T149 [P] [US5] Create TunnelForm component in frontend/src/components/tunnels/TunnelForm.tsx (create/edit tunnel config)
- [ ] T150 [P] [US5] Create TunnelStatus component in frontend/src/components/tunnels/TunnelStatus.tsx (real-time status indicator)
- [ ] T151 [US5] Create tunnels page in frontend/src/pages/tunnels.tsx (integrate components)
- [ ] T152 [P] [US5] Create useTunnels hook in frontend/src/hooks/useTunnels.ts (tunnel state management)
- [ ] T153 [US5] Create frontend/public/tunnels.html entry point

### Integration Tests for User Story 5

- [ ] T154 [US5] Integration test for tunnel creation and status in backend/tests/integration/test_tunnel_lifecycle.py
- [ ] T155 [US5] Integration test for tunnel auto-reconnection in backend/tests/integration/test_tunnel_reconnection.py

**Checkpoint**: User Story 5 (Tunnels) is fully functional

---

## Phase 8: User Story 6 - SSH Command Snippets (Priority: P3)

**Goal**: Users save, organize, and execute command snippets across multiple terminal sessions

**Independent Test**: Can be tested by verifying: User creates snippet → Executes in terminal → Output appears → Broadcasts to multiple sessions

### Contract Tests for User Story 6

- [ ] T156 [P] [US6] Contract test for POST /snippets in backend/tests/contract/test_snippets.py (verify snippet creation)
- [ ] T157 [P] [US6] Contract test for GET /snippets in backend/tests/contract/test_snippets.py (verify snippet list)
- [ ] T158 [P] [US6] Contract test for POST /snippets/{snippet_id}/execute in backend/tests/contract/test_snippets.py (verify execution)
- [ ] T159 [P] [US6] Contract test for PUT /snippets/{snippet_id} in backend/tests/contract/test_snippets.py (verify update)
- [ ] T160 [P] [US6] Contract test for DELETE /snippets/{snippet_id} in backend/tests/contract/test_snippets.py (verify deletion)

### Backend Implementation for User Story 6

- [ ] T161 [P] [US6] Implement SnippetService in backend/src/services/snippet_service.py (CRUD, execution, broadcast)
- [ ] T162 [US6] Implement snippet endpoints in backend/src/api/snippets.py:
  - POST /snippets (create snippet)
  - GET /snippets (list snippets with filtering)
  - PUT /snippets/{snippet_id} (update snippet)
  - DELETE /snippets/{snippet_id}
  - POST /snippets/{snippet_id}/execute (execute in a terminal session)
  - POST /snippets/{snippet_id}/broadcast (execute in multiple sessions)
- [ ] T163 [P] [US6] Create schemas in backend/src/schemas/snippets.py (SnippetCreate, SnippetUpdate, SnippetResponse, SnippetExecuteRequest)
- [ ] T164 [US6] Implement snippet execution with terminal session targeting
- [ ] T165 [US6] Implement broadcast execution to multiple terminal sessions (send command to each via WebSocket)
- [ ] T166 [US6] Add snippet operation audit logging

### Frontend Implementation for User Story 6

- [ ] T167 [P] [US6] Create SnippetLibrary component in frontend/src/components/snippets/SnippetLibrary.tsx (list snippets, organize by tags)
- [ ] T168 [P] [US6] Create SnippetForm component in frontend/src/components/snippets/SnippetForm.tsx (create/edit snippets)
- [ ] T169 [P] [US6] Create SnippetExecutor component in frontend/src/components/snippets/SnippetExecutor.tsx (select sessions, execute, show results)
- [ ] T170 [US6] Create snippets feature in terminal page (embed SnippetLibrary + quick execute buttons)
- [ ] T171 [P] [US6] Create useSnippets hook in frontend/src/hooks/useSnippets.ts (snippet state, API calls)
- [ ] T172 [P] [US6] Integrate snippet execution with terminal WebSocket (send command via TerminalService)

### Integration Tests for User Story 6

- [ ] T173 [US6] Integration test for snippet creation and execution in backend/tests/integration/test_snippet_lifecycle.py
- [ ] T174 [US6] Integration test for snippet broadcast to multiple sessions in backend/tests/integration/test_snippet_broadcast.py

**Checkpoint**: All User Stories (1-6) are now complete and independently functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements, testing, documentation, and deployment preparation

### Admin Panel & Session Management

- [ ] T175 Implement admin dashboard in backend/src/api/admin.py:
  - GET /admin/users (list users with roles, last login)
  - GET /admin/sessions (list active sessions across all users)
  - DELETE /admin/sessions/{session_id} (terminate user session)
  - POST /admin/settings/oidc-providers (configure SSO providers)
  - GET /admin/settings/oidc-providers (list providers)
- [ ] T176 Create admin UI components in frontend/src/components/admin/:
  - UserManagement.tsx (user list, role assignment)
  - SessionManager.tsx (active session list, termination)
  - OIDCProviderSettings.tsx (provider configuration form)
- [ ] T177 Create admin page in frontend/src/pages/admin.tsx
- [ ] T178 Create frontend/public/admin.html entry point

### OIDC Provider Configuration

- [ ] T179 Implement OIDC provider CRUD in backend/src/api/admin.py (store in OIDCProvider table)
- [ ] T180 Implement OIDC login handler in backend/src/api/auth.py (dynamic provider lookup from DB)
- [ ] T181 Update OIDC service to load providers from database (replace env var approach)
- [ ] T182 Implement provider configuration validation (ensure valid discovery_url)

### Comprehensive Testing

- [ ] T183 [P] Run all contract tests in backend/tests/contract/ and verify pass rate ≥95%
- [ ] T184 [P] Run all integration tests in backend/tests/integration/ and verify pass rate ≥95%
- [ ] T185 [P] Run frontend unit tests in frontend/tests/unit/ and verify pass rate ≥90%
- [ ] T186 [P] Run frontend E2E tests with Playwright in frontend/tests/e2e/ covering critical paths:
  - Auth flow (login, SSO, logout)
  - Host creation and search
  - Terminal creation and command execution
  - File upload/download
  - Tunnel creation
  - Snippet execution
- [ ] T187 Measure test coverage:
  - Backend: ≥80% for security-critical paths (auth, SSH, SFTP, permissions)
  - Frontend: ≥70% for critical components (auth, terminal, file manager)
- [ ] T188 Run security scanning (OWASP Top 10 checklist):
  - SQL injection: Verify parameterized queries via SQLAlchemy ORM
  - XSS: Verify React auto-escaping + DomPurify for user content
  - CSRF: Verify CORS whitelist + SameSite cookies
  - Authentication: Verify JWT expiration (1h) + session cleanup
  - Data exposure: Verify no sensitive data in logs or responses
  - Known vulnerabilities: Run dependabot checks
- [ ] T189 Performance testing:
  - Terminal latency: Verify p95 ≤100ms command-to-output
  - File transfer: Verify ≥5 MB/s on local networks
  - Dashboard load: Verify ≤2s page load time
  - Concurrent connections: Load test ≥100 users with ≥10 terminal sessions each

### Documentation & Deployment

- [ ] T190 Update README.md with:
  - Project overview and architecture diagram
  - Quick start instructions (Docker Compose)
  - Development setup (local, testing)
  - API documentation link (Swagger UI)
  - Deployment instructions (production, scaling)
- [ ] T191 Create CONTRIBUTING.md with development workflow, code standards, PR process
- [ ] T192 Create API documentation from OpenAPI spec (Swagger UI at /docs, ReDoc at /redoc)
- [ ] T193 [P] Create architecture documentation in docs/ARCHITECTURE.md
- [ ] T194 [P] Create deployment guide in docs/DEPLOYMENT.md (Docker, Kubernetes, SSL setup)
- [ ] T195 [P] Create troubleshooting guide in docs/TROUBLESHOOTING.md (common issues, solutions)
- [ ] T196 Validate quickstart.md guide by following all steps (Docker Compose, local setup)
- [ ] T197 Create database backup/restore documentation in docs/DATABASE.md
- [ ] T198 Setup CI/CD pipeline validation (GitHub Actions workflows execute successfully)

### Code Quality & Refinement

- [ ] T199 [P] Code cleanup: Remove console.logs, debug code from backend
- [ ] T200 [P] Code cleanup: Remove console.logs, debug code from frontend
- [ ] T201 Run full backend linting/formatting suite and fix all warnings
- [ ] T202 Run full frontend linting/formatting suite and fix all warnings
- [ ] T203 Refactor duplicate code identified during implementation
- [ ] T204 Optimize database queries: Add missing indexes, verify N+1 queries eliminated
- [ ] T205 Optimize frontend bundle sizes: Verify Vite chunks are <100KB each
- [ ] T206 [P] Add missing error handling edge cases identified during testing
- [ ] T207 [P] Add missing input validation for all user-facing endpoints

### Security Hardening

- [ ] T208 Verify encryption configuration:
  - ENCRYPTION_MASTER_KEY generated securely (≥32 bytes)
  - Credentials encrypted at-rest with AES-256-GCM
  - No plaintext credentials in logs/responses
- [ ] T209 Verify authentication security:
  - JWT tokens expire after 1 hour
  - Tokens not exposed in logs
  - Session cleanup on logout
  - Failed login attempts rate-limited (max 5/min per IP)
- [ ] T210 Verify HTTPS/TLS:
  - All endpoints require HTTPS in production
  - TLS 1.3 enforced
  - SSL certificate configured
  - HSTS header enabled
- [ ] T211 Verify CORS configuration:
  - Explicit whitelist (no wildcards)
  - Credentials flag set appropriately
  - Preflight requests validated
- [ ] T212 Verify audit logging:
  - All user actions logged with timestamp, user, session, action, IP, user agent
  - No sensitive data (passwords, keys, tokens) in audit logs
  - Audit logs retained ≥90 days
- [ ] T213 Verify permission boundaries:
  - Users cannot access hosts not assigned to them
  - Users cannot escalate privileges
  - Permission changes require admin action
- [ ] T214 Add rate limiting on all endpoints (configurable per endpoint)

### Final Validation

- [ ] T215 End-to-end validation test:
  - Admin user creates 3 SSH hosts
  - Regular user opens terminal, executes commands
  - User uploads/downloads files
  - User creates port forwards
  - User saves and executes snippets
  - All operations audit logged correctly
- [ ] T216 Performance validation:
  - Dashboard loads in <2s
  - Terminal response <100ms p95
  - File transfer >5 MB/s
  - ≥100 concurrent users supported
- [ ] T217 Security validation:
  - OWASP Top 10 vulnerabilities scanned and fixed
  - Penetration testing (basic): SQL injection, XSS, CSRF attempts all blocked
  - Credential storage verified encrypted
- [ ] T218 Deployment validation:
  - Docker Compose deployment successful
  - All services healthy and responding
  - Database migrations applied successfully
  - Swagger UI accessible at /docs
- [ ] T219 Documentation validation:
  - README complete and accurate
  - Quickstart guide tested and works
  - API docs comprehensive
  - Deployment guide clear
- [ ] T220 Create CHANGELOG.md with all features, bug fixes, security notes for v0.1.0

**Checkpoint**: Termone MVP (Phase 1) is production-ready

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - P1 stories (1, 2, 3): Can proceed in parallel
  - P2 stories (4, 5): Can start after P1 stories complete
  - P3 stories (6): Can start after P2 stories complete
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### Critical Path

1. Phase 1: Setup (T001-T010) - **Must complete first**
2. Phase 2: Foundational (T011-T045) - **Blocks all stories, ~150-200 hours**
3. Phase 3: User Story 1 (T046-T071) - **P1, MVP, ~80-100 hours**
4. Phase 4: User Story 2 (T072-T094) - **P1, MVP, ~100-120 hours**
5. Phase 5: User Story 3 (T095-T113) - **P1, MVP, ~80-100 hours**
6. Validate and deploy P1 MVP
7. Phase 6: User Story 4 (T114-T136) - **P2, ~100-120 hours**
8. Phase 7: User Story 5 (T137-T155) - **P2, ~60-80 hours**
9. Phase 8: User Story 6 (T156-T174) - **P3, ~60-80 hours**
10. Phase 9: Polish (T175-T220) - **~100-150 hours**

### Within Each User Story

- Contract tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Integration tests MUST pass before story is considered complete
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**: All [P] tasks can run in parallel:
- T002, T003, T004, T005 can all run together
- T006-T010 depend on prior tasks but some can parallelize

**Phase 2 (Foundational)**: After T011 (database setup):
- Database models (T015a-f) can all run in parallel
- Auth services (T016-T022) can parallelize after models
- API framework (T023-T027) can run in parallel
- Real-time infrastructure (T028-T030) can parallelize
- Frontend setup (T031-T040) fully independent of backend

**Phase 3+ (User Stories)**: After Phase 2 completion:
- Contract tests [P] can all run in parallel
- Models [P] can run in parallel
- Once Foundational phase completes, **all user stories can start in parallel** (if team capacity allows)
- E.g., Team of 3 developers:
  - Dev A: User Story 1
  - Dev B: User Story 2
  - Dev C: User Story 3

### Suggested Delivery Schedule (Single Developer)

1. **Weeks 1-2**: Setup + Foundational (40-50 hours)
2. **Weeks 3-4**: User Story 1 (20-25 hours) → Validate MVP
3. **Week 5**: User Story 2 (25-30 hours)
4. **Week 6**: User Story 3 (20-25 hours) → Full P1 MVP ready
5. **Weeks 7-8**: User Story 4 (25-30 hours)
6. **Week 9**: User Story 5 (15-20 hours)
7. **Week 10**: User Story 6 (15-20 hours)
8. **Weeks 11-12**: Polish & Testing (25-40 hours) → Production ready

**Total estimate: 12-14 weeks / ~200-250 hours** for one developer

### Suggested Delivery Schedule (3-Developer Team)

1. **Week 1**: All 3 devs: Setup + Foundational (10-15 hours parallel work)
2. **Weeks 2-3**: Dev A: US1, Dev B: US2, Dev C: US3 (parallel)
3. **Week 4**: Integrate + validate P1 MVP
4. **Weeks 5-6**: Dev A: US4, Dev B: US5, Dev C: US6 (parallel)
5. **Week 7**: All 3 devs: Polish & Testing

**Total estimate: 7 weeks / ~80-100 hours per developer** with parallel execution

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (2-3 days)
2. Complete Phase 2: Foundational (5-7 days) - **CRITICAL**
3. Complete Phase 3: User Story 1 (3-5 days)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy MVP if approved

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently
6. Add User Story 5 → Test independently
7. Add User Story 6 → Test independently
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With 3+ developers:

1. All team members: Complete Setup + Foundational together (1 week)
2. Once Foundational is done:
   - **Developer A**: User Stories 1 + 4 (Host Manager + File Manager)
   - **Developer B**: User Stories 2 + 5 (Terminal + Tunnels)
   - **Developer C**: User Stories 3 + 6 (Stats + Snippets)
3. Stories complete and integrate independently
4. Week 7: All team members on Polish & Testing

---

## Notes

- Tasks are organized by user story to enable **independent implementation and testing**
- Each user story can be deployed separately as a feature increment
- Phase 2 (Foundational) is the critical path - it blocks all user stories
- Contract tests MUST be written before implementation (TDD approach for security-critical paths)
- [P] tasks = can run in parallel (different files, no dependencies)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Verify tests fail before implementing (TDD discipline)
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

**Status**: ✅ Ready for implementation
**Total Tasks**: 220
**Estimated Effort**: 200-250 hours (single developer) / 80-100 hours per developer (3-person team)
**Critical Path**: Phase 1 → Phase 2 → P1 Stories → Validate MVP → P2 Stories → P3 Stories → Polish

Execute tasks in priority order:
1. **Immediate**: Phase 1 Setup (T001-T010)
2. **Blocking**: Phase 2 Foundational (T011-T045)
3. **P1 MVP**: User Stories 1, 2, 3 (T046-T113) - deploy after validating
4. **P2 Features**: User Stories 4, 5 (T114-T155)
5. **P3 Enhancement**: User Story 6 (T156-T174)
6. **Final**: Polish & Testing (T175-T220)
