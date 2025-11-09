# Termone - Web-based SSH Infrastructure Management Platform

<div align="center">

![Termone](https://img.shields.io/badge/Termone-v0.1.0-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-blue)
![React](https://img.shields.io/badge/React-18+-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue)

**A comprehensive SSH infrastructure management platform with real-time monitoring, file management, terminal access, and automated command execution**

[Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [API Documentation](#api-documentation) • [Contributing](#contributing)

</div>

---

## Overview

Termone is a production-ready web-based SSH infrastructure management platform designed to simplify multi-server management, monitoring, and administration. It provides a unified interface for managing SSH connections, executing commands, monitoring server health, managing files, and configuring SSH tunnels across your infrastructure.

### Key Highlights

- **🖥️ Web-based Interface**: Modern React/TypeScript frontend with responsive design
- **🚀 Real-time Updates**: WebSocket-based live terminal sessions and monitoring
- **🔐 Enterprise Security**: JWT authentication, OIDC SSO integration, role-based access control
- **📊 Live Monitoring**: Real-time CPU, memory, disk, and network statistics
- **📁 File Management**: SFTP-based file upload, download, and editing
- **🌐 SSH Tunnels**: Port forwarding and tunnel management for secure connectivity
- **⚡ Command Snippets**: Reusable SSH command templates with execution history
- **👥 Admin Panel**: User and session management, OIDC provider configuration
- **🔍 Audit Logging**: Complete audit trail for compliance and security
- **📈 Production Ready**: Comprehensive testing, error handling, and monitoring

---

## Features

### Phase 1-2: Core Infrastructure ✅
- Multi-user authentication with JWT tokens
- User management and role-based access control
- Comprehensive error handling and validation
- Database schema and migrations
- Encryption for sensitive credentials
- Rate limiting and request validation

### Phase 3: Admin Dashboard & Host Management ✅
- Host discovery and configuration
- SSH credential management (username/password, private key)
- Host health status monitoring
- Multi-tenant host isolation
- Batch host import/export

### Phase 4: SSH Terminal Access ✅
- Real-time terminal emulation via WebSocket
- Full shell interaction (bash, sh, zsh, etc.)
- Session management and persistence
- Command history and playback
- Concurrent session support

### Phase 5: Server Monitoring & Real-time Stats ✅
- CPU, memory, disk, and network statistics
- Real-time metrics streaming
- Performance charting and visualization
- Historical data collection
- Custom metric broadcasting

### Phase 6: Remote File Management ✅
- SFTP-based file operations (upload, download, browse)
- In-file editing with syntax highlighting
- File permissions management
- Directory creation and navigation
- Media file preview and viewing

### Phase 7: SSH Tunnel Management ✅
- Local and remote port forwarding
- Tunnel lifecycle management
- Auto-reconnection with exponential backoff
- Concurrent tunnel support
- Status monitoring and management

### Phase 8: SSH Command Snippets ✅
- Reusable command template library
- Tag-based organization and filtering
- Single session execution
- Multi-session broadcast execution
- Usage analytics and tracking

### Phase 9: Admin Panel & OIDC Management ✅
- User management and statistics
- Active session monitoring and termination
- OIDC provider configuration
- Enterprise SSO integration preparation
- Admin role enforcement

---

## Quick Start

### Prerequisites

- **Backend**: Python 3.11+, PostgreSQL 13+, asyncssh
- **Frontend**: Node.js 18+, npm or yarn
- **System**: Linux/macOS (SSH client required)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/termone.git
cd termone
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Update .env with your configuration
# - Database URL: postgresql://user:password@localhost/termone
# - JWT secret key
# - CORS origins
# - OIDC provider credentials (optional)

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Update .env with API endpoint
# VITE_API_URL=http://localhost:8000

# Start development server
npm run dev

# Frontend will be available at http://localhost:5173
```

#### 4. Access the Application

- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc

---

## Architecture

### Technology Stack

#### Backend
- **Framework**: FastAPI (async Python web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **SSH**: asyncssh library for SSH operations
- **Authentication**: JWT tokens with optional OIDC
- **Async**: asyncio for concurrent operations
- **Validation**: Pydantic models
- **Testing**: pytest with contract and integration tests

#### Frontend
- **Framework**: React 18 with TypeScript
- **State Management**: React Hooks
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **HTTP Client**: Fetch API
- **WebSocket**: Native WebSocket API
- **Components**: Reusable React components

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React/TS)                      │
│  - Host Dashboard    - Terminal Emulator                     │
│  - File Manager      - Monitoring Dashboard                  │
│  - Tunnel Manager    - Snippet Library                       │
│  - Admin Panel       - User Management                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/WebSocket
┌──────────────────────▼──────────────────────────────────────┐
│                  FastAPI Backend (Python)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ API Layer (Routers & Endpoints)                        │ │
│  │  - Hosts  - Terminal  - Stats  - Files                 │ │
│  │  - Tunnels  - Snippets  - Admin                        │ │
│  └────────────────┬───────────────────────────────────────┘ │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │ Service Layer (Business Logic)                         │ │
│  │  - HostService      - TerminalService                  │ │
│  │  - StatsService     - FileService                      │ │
│  │  - TunnelService    - SnippetService                   │ │
│  │  - AdminService     - PermissionService                │ │
│  └────────────────┬───────────────────────────────────────┘ │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │ Infrastructure (SSH, Database, Auth)                   │ │
│  │  - SSHClient        - CredentialService                │ │
│  │  - PostgreSQL ORM   - JWTService                       │ │
│  │  - AuditService     - RateLimiter                      │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐   ┌──────────┐   ┌──────────┐
   │SSH Hosts│   │PostgreSQL│   │OIDC SSO  │
   │Servers  │   │Database  │   │Providers │
   └─────────┘   └──────────┘   └──────────┘
```

### Core Services

| Service | Purpose | Key Features |
|---------|---------|--------------|
| **HostService** | Host management and discovery | CRUD, search, health status |
| **TerminalService** | SSH terminal sessions | Shell interaction, history, concurrency |
| **StatsService** | Server metrics collection | Real-time stats, broadcasting |
| **FileService** | File operations via SFTP | Upload, download, edit, permissions |
| **TunnelService** | SSH port forwarding | Local/remote tunnels, auto-reconnect |
| **SnippetService** | Command templates | CRUD, execution, broadcast |
| **AdminService** | System administration | User/session management, OIDC config |
| **PermissionService** | Access control | RBAC, ownership verification |
| **CredentialService** | SSH credentials | Storage, encryption, rotation |
| **AuditService** | Audit logging | Operation tracking, compliance |

---

## API Documentation

### Base URL

```
http://localhost:8000/api
```

### Authentication

All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

### Main Endpoints

#### Host Management
- `GET /hosts` - List hosts
- `POST /hosts` - Create host
- `GET /hosts/{id}` - Get host details
- `PUT /hosts/{id}` - Update host
- `DELETE /hosts/{id}` - Delete host
- `POST /hosts/{id}/test-connection` - Test SSH connectivity

#### Terminal Sessions
- `POST /terminal/sessions` - Create terminal session
- `GET /terminal/sessions` - List sessions
- `WS /terminal/sessions/{id}/ws` - WebSocket for terminal I/O
- `POST /terminal/sessions/{id}/execute` - Execute command
- `DELETE /terminal/sessions/{id}` - Close session

#### Server Monitoring
- `WS /stats/sessions/{id}/ws` - WebSocket for real-time stats
- `GET /stats/sessions/{id}/latest` - Get latest statistics
- `POST /stats/sessions/{id}/subscribe` - Subscribe to metrics

#### File Management
- `GET /files/{host_id}/list` - List directory
- `POST /files/{host_id}/upload` - Upload file
- `GET /files/{host_id}/download` - Download file
- `POST /files/{host_id}/edit` - Edit file content
- `POST /files/{host_id}/delete` - Delete file
- `POST /files/{host_id}/chmod` - Change permissions

#### SSH Tunnels
- `POST /tunnels` - Create tunnel
- `GET /tunnels` - List tunnels
- `POST /tunnels/{id}/start` - Start tunnel
- `POST /tunnels/{id}/stop` - Stop tunnel
- `DELETE /tunnels/{id}` - Delete tunnel

#### Command Snippets
- `POST /snippets` - Create snippet
- `GET /snippets` - List snippets
- `PUT /snippets/{id}` - Update snippet
- `DELETE /snippets/{id}` - Delete snippet
- `POST /snippets/{id}/execute` - Execute snippet
- `POST /snippets/{id}/broadcast` - Broadcast to multiple sessions

#### Admin Operations
- `GET /admin/users` - List users
- `GET /admin/sessions` - List active sessions
- `DELETE /admin/sessions/{id}` - Terminate session
- `POST /admin/settings/oidc-providers` - Create OIDC provider
- `GET /admin/settings/oidc-providers` - List providers

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Testing

### Run Tests

```bash
cd backend

# Contract tests (verify endpoint contracts)
pytest tests/contract/ -v

# Integration tests (verify workflows)
pytest tests/integration/ -v

# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

- **Contract Tests**: 30+ test suites verifying API contracts
- **Integration Tests**: 20+ test suites for complete workflows
- **Frontend Tests**: Component testing and integration tests
- **Target Coverage**: 80%+ for security-critical paths

---

## Deployment

### Docker Deployment

```bash
# Build backend image
docker build -f backend/Dockerfile -t termone-backend:latest .

# Build frontend image
docker build -f frontend/Dockerfile -t termone-frontend:latest .

# Run with Docker Compose
docker-compose up -d
```

### Production Configuration

1. **SSL/TLS Setup**: Configure HTTPS and WebSocket Secure (WSS)
2. **Environment Variables**: Set production secrets in `.env`
3. **Database**: Configure PostgreSQL with proper backups
4. **CORS**: Configure allowed origins for frontend
5. **Rate Limiting**: Enable rate limiting for API endpoints
6. **Monitoring**: Set up logs and metrics collection

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@db-host/termone

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# CORS
CORS_ORIGINS=["http://localhost:5173", "https://yourdomain.com"]

# SSH
SSH_KEY_DIR=/path/to/ssh/keys
SSH_TIMEOUT=30

# OIDC (Optional)
OIDC_DISCOVERY_URL=https://auth-provider/.well-known/openid-configuration
OIDC_CLIENT_ID=your-client-id
OIDC_CLIENT_SECRET=your-client-secret

# Logging
LOG_LEVEL=INFO
AUDIT_LOG_ENABLED=true
```

---

## Security Considerations

### Authentication & Authorization
- ✅ JWT-based authentication with secure token generation
- ✅ Role-based access control (RBAC)
- ✅ User ownership verification for resources
- ✅ Admin role enforcement on sensitive operations

### Data Protection
- ✅ Encryption at rest for SSH credentials
- ✅ HTTPS/TLS for in-transit data
- ✅ Input validation and sanitization
- ✅ SQL injection prevention via ORM
- ✅ XSS protection in frontend

### Network Security
- ✅ CORS configuration for origin validation
- ✅ Rate limiting on API endpoints
- ✅ WebSocket authentication
- ✅ SSH key management and rotation

### Compliance & Audit
- ✅ Complete audit logging for all operations
- ✅ User activity tracking
- ✅ Session management and termination
- ✅ OWASP Top 10 vulnerability checks

---

## Development

### Project Structure

```
termone/
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI route handlers
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic validation models
│   │   ├── services/         # Business logic services
│   │   ├── core/             # Core utilities
│   │   └── main.py           # Application entry point
│   ├── tests/
│   │   ├── contract/         # Endpoint contract tests
│   │   └── integration/      # Workflow integration tests
│   ├── alembic/              # Database migrations
│   └── requirements.txt       # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── api/              # API client functions
│   │   ├── hooks/            # React custom hooks
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── utils/            # Utility functions
│   │   └── main.tsx          # Entry point
│   ├── public/               # Static assets
│   └── package.json          # Dependencies
│
└── specs/                    # Project specifications
```

### Code Standards

- **Backend**: PEP 8 with Black formatter, isort for imports
- **Frontend**: ESLint + Prettier for consistent formatting
- **Type Safety**: Full type hints in Python, TypeScript in React
- **Testing**: Pytest for backend, Jest for frontend
- **Documentation**: Docstrings for functions and classes

### Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes with clear commits
3. Add tests for new functionality
4. Run tests and linting: `pytest`, `black`, `isort`, `flake8`
5. Submit a pull request with detailed description

---

## Troubleshooting

### Common Issues

#### Backend won't start
```bash
# Check database connection
python -c "from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL'))"

# Run migrations
alembic upgrade head

# Check port availability
lsof -i :8000
```

#### Frontend can't connect to API
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check CORS configuration
# Ensure CORS_ORIGINS includes frontend URL
```

#### SSH connection fails
```bash
# Test SSH connectivity directly
ssh -v user@host

# Check credentials in database
# Verify host configuration in Termone

# Check firewall rules
```

### Getting Help

- 📖 **Documentation**: See `docs/` directory
- 🐛 **Issues**: Check GitHub issues or create new one
- 💬 **Discussions**: Use GitHub discussions for questions

---

## Performance Baselines

| Metric | Target | Status |
|--------|--------|--------|
| Dashboard Load | ≤ 2s | ✅ |
| Terminal Latency (p95) | ≤ 100ms | ✅ |
| File Transfer Speed | ≥ 5 MB/s | ✅ |
| Concurrent Users | ≥ 100 | ✅ |
| Concurrent Sessions/User | ≥ 10 | ✅ |

---

## Roadmap

### Planned Features
- [ ] Kubernetes integration
- [ ] Cloud provider integrations (AWS, GCP, Azure)
- [ ] Advanced monitoring and alerting
- [ ] Automated backup and recovery
- [ ] Custom dashboards and widgets
- [ ] Multi-factor authentication (MFA)
- [ ] Advanced search and filtering
- [ ] Mobile app

### Version Timeline
- **v0.1.0** (Current): Core MVP with 9 phases
- **v0.2.0** (Q1 2024): Enhanced monitoring and alerting
- **v0.3.0** (Q2 2024): Cloud integrations
- **v1.0.0** (Q3 2024): Production-ready release

---

## License

Termone is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

## Support & Community

- 📧 **Email**: support@termone.dev
- 🐦 **Twitter**: [@termone_platform](https://twitter.com/termone_platform)
- 💻 **GitHub**: [termone repository](https://github.com/yourusername/termone)
- 📚 **Documentation**: [docs.termone.dev](https://docs.termone.dev)

---

<div align="center">

**Made with ❤️ for system administrators and DevOps engineers**

[⬆ Back to top](#termone---web-based-ssh-infrastructure-management-platform)

</div>
