# Termone Development Quickstart Guide

**Updated**: 2025-11-08
**Status**: Ready for implementation

This guide covers local development setup for Termone platform (backend + frontend + database).

## Prerequisites

- Docker & Docker Compose (v2.20+)
- Python 3.11+ (for backend development)
- Node.js 18+ (for frontend development)
- Git
- SSH client (for testing terminal features)
- PostgreSQL 14+ client tools (psql, optional for debugging)

## Quick Start (Docker Compose)

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/termone.git
cd termone
git checkout 001-termone-core

# Create environment file
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env`:
```bash
# Encryption
ENCRYPTION_MASTER_KEY=<generate-32-byte-hex-key>  # openssl rand -hex 32

# JWT
JWT_SECRET=<generate-random-secret>  # openssl rand -base64 32

# Database
DATABASE_URL=postgresql://termone:termone@postgres:5432/termone
POSTGRES_PASSWORD=<secure-password>

# OIDC (optional for initial dev)
OIDC_DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration
OIDC_CLIENT_ID=<your-google-oauth-client-id>
OIDC_CLIENT_SECRET=<your-google-oauth-secret>

# Environment
APP_ENV=development
DEBUG=true
```

### 3. Start Services

```bash
# Build and start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 4. Initialize Database

```bash
# Run migrations (Alembic)
docker exec termone-backend alembic upgrade head

# Seed test data (development only)
docker exec termone-backend python -m backend.database.seeders
```

### 5. Access the Application

```
Frontend: http://localhost:5173
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs (Swagger UI)
Postgres: localhost:5432
```

### Test Credentials (Development Only)

```
Admin User:
  Email: admin@termone.io
  Password: admin123

Regular User:
  Email: user@termone.io
  Password: user123

Sample SSH Hosts (pre-configured):
  - Local Test Server (localhost:22)
  - Public Demo Server (demo.example.com:22)
```

---

## Local Development (Without Docker)

### Backend Setup

#### 1. Python Virtual Environment

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Database Setup

```bash
# Start PostgreSQL locally (or use existing instance)
# Set DATABASE_URL environment variable
export DATABASE_URL=postgresql://user:password@localhost:5432/termone

# Run migrations
alembic upgrade head

# Seed test data
python -m backend.database.seeders
```

#### 3. Start Backend Server

```bash
# Ensure venv is activated
source venv/bin/activate

# Set environment variables
export ENCRYPTION_MASTER_KEY=$(openssl rand -hex 32)
export JWT_SECRET=$(openssl rand -base64 32)
export DATABASE_URL=postgresql://user:password@localhost:5432/termone
export APP_ENV=development

# Run FastAPI server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Server will be available at http://localhost:8000
# Auto-reload on code changes
```

### Frontend Setup

#### 1. Node Dependencies

```bash
cd frontend

# Install dependencies
npm install

# Or with yarn
yarn install
```

#### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env.local

# Edit .env.local
# VITE_API_URL=http://localhost:8000/api
```

#### 3. Start Development Server

```bash
# Start Vite dev server with hot reload
npm run dev

# or yarn
yarn dev

# Frontend will be available at http://localhost:5173
```

---

## Testing

### Backend Tests

```bash
cd backend

# Activate venv
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/contract/test_auth.py

# Run tests in watch mode
pytest-watch
```

**Test Categories**:
- `tests/unit/` - Unit tests (models, services, utilities)
- `tests/contract/` - API contract tests (endpoint validation)
- `tests/integration/` - End-to-end workflow tests (auth flow, SSH tunnel, etc.)

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm run test

# Run with coverage
npm run test:coverage

# Run E2E tests with Playwright
npm run test:e2e

# Run E2E tests in UI mode (interactive)
npm run test:e2e --ui
```

### Manual Testing

#### 1. Test SSH Connection

```bash
# Create a test SSH host pointing to localhost
# Auth type: password or SSH key

# From terminal page:
# - Click "Open Terminal" for the test host
# - Try command: `whoami`, `ls`, `echo "Hello from xterm.js"`
# - Verify output appears within 100ms
```

#### 2. Test File Manager

```bash
# From file manager page for test host:
# - List files: should show current directory
# - Upload: drag/drop a file
# - Edit: open a text file in Monaco editor
# - Download: download a file
```

#### 3. Test Real-time Stats

```bash
# From stats page:
# - Should see CPU, memory, disk charts updating every 5 seconds
# - Leave open for 2+ minutes, verify data points accumulate
```

#### 4. Test WebSocket Reconnection

```bash
# Open terminal, keep it open
# Disconnect network (unplug ethernet or WiFi)
# Wait 5-10 seconds, reconnect network
# Terminal should restore automatically (within 30s)
```

---

## Code Structure Overview

### Backend

```
backend/
├── src/
│   ├── api/              # FastAPI route handlers
│   ├── models/           # SQLAlchemy ORM models
│   ├── services/         # Business logic (auth, SSH, encryption)
│   ├── middleware/       # JWT validation, CORS, rate limiting
│   ├── database/         # Migrations, seeders
│   ├── config.py         # Environment configuration
│   └── main.py           # FastAPI app
├── tests/                # Unit, contract, integration tests
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container image
└── alembic.ini          # Migration config
```

**Key Files for Implementation**:
- `src/api/auth.py` - Authentication endpoints (login, SSO, 2FA)
- `src/api/terminal.py` - WebSocket terminal handler
- `src/services/ssh_client.py` - SSH connection wrapper
- `src/services/encryption.py` - Credential encryption/decryption
- `src/services/audit.py` - Structured logging

### Frontend

```
frontend/
├── src/
│   ├── pages/            # Page entry points (auth, dashboard, terminal, etc.)
│   ├── components/       # React components organized by feature
│   ├── services/         # API client, WebSocket manager
│   ├── hooks/            # Custom React hooks
│   ├── context/          # React Context for state (auth, theme)
│   ├── types/            # TypeScript type definitions
│   ├── i18n/             # i18next translations (en, ko)
│   └── utils/            # Utilities (formatting, validation, errors)
├── public/               # Static HTML entry points for each page
├── tests/                # Unit, integration, E2E tests
├── package.json          # Dependencies
├── vite.config.ts        # Vite bundler config (MPA setup)
└── Dockerfile            # Container image
```

**Key Files for Implementation**:
- `src/pages/auth.tsx` - Login/SSO/2FA page
- `src/pages/terminal.tsx` - Terminal page with xterm.js
- `src/components/terminal/` - Terminal-related components
- `src/services/websocket.ts` - WebSocket manager for real-time features
- `src/services/api.ts` - HTTP client for REST API calls

---

## Useful Commands

### Database

```bash
# Connect to PostgreSQL
psql postgresql://user:password@localhost:5432/termone

# View tables
\dt

# View migrations
docker exec termone-backend alembic current
docker exec termone-backend alembic history

# Reset database (development only!)
docker exec termone-backend alembic downgrade base
docker exec termone-backend alembic upgrade head
```

### Docker

```bash
# View service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Access container shell
docker exec -it termone-backend bash
docker exec -it termone-frontend bash
docker exec -it termone-postgres bash

# Stop all services
docker-compose down

# Clean up (remove volumes)
docker-compose down -v
```

### FastAPI

```bash
# Access Swagger UI
http://localhost:8000/docs

# Access ReDoc
http://localhost:8000/redoc

# Check OpenAPI schema
curl http://localhost:8000/openapi.json | jq .
```

---

## Common Issues & Solutions

### Issue: Database connection refused

**Solution**:
```bash
# Ensure postgres service is running
docker-compose ps postgres

# Check DATABASE_URL in .env
echo $DATABASE_URL

# Verify postgres is accepting connections
psql $DATABASE_URL -c "SELECT 1"
```

### Issue: ENCRYPTION_MASTER_KEY not set

**Solution**:
```bash
# Generate a new key
ENCRYPTION_MASTER_KEY=$(openssl rand -hex 32)
export ENCRYPTION_MASTER_KEY
echo $ENCRYPTION_MASTER_KEY  # Save this securely!
```

### Issue: Frontend can't reach backend API

**Solution**:
```bash
# Check VITE_API_URL in .env.local
cat frontend/.env.local

# Ensure backend is running
curl http://localhost:8000/health

# Clear browser cache and reload
# (Ctrl+Shift+Delete in Chrome)
```

### Issue: SSH connection failed when testing

**Solution**:
```bash
# Create a test SSH key
ssh-keygen -t ed25519 -f ~/.ssh/id_test -N ""

# Add public key to authorized_keys
cat ~/.ssh/id_test.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Register in Termone:
# Host: localhost
# Port: 22
# Username: your-username
# Auth: key
# (paste contents of ~/.ssh/id_test)
```

---

## Next Steps

1. **Run Tests**: Execute test suite to verify setup
   ```bash
   cd backend && pytest
   cd ../frontend && npm run test
   ```

2. **Manual Testing**: Follow the testing section above

3. **Code Navigation**: Review code structure and key files

4. **Implementation**: Start with Phase 2 tasks (`/speckit.tasks`)

5. **Documentation**: Update API docs if needed

---

## Further Reading

- **Backend**: [FastAPI Docs](https://fastapi.tiangolo.com/)
- **Frontend**: [React Docs](https://react.dev/), [Vite Docs](https://vitejs.dev/)
- **Database**: [SQLAlchemy ORM](https://docs.sqlalchemy.org/), [Alembic](https://alembic.sqlalchemy.org/)
- **Testing**: [pytest](https://docs.pytest.org/), [Vitest](https://vitest.dev/)
- **SSH**: [asyncssh](https://asyncssh.readthedocs.io/), [xterm.js](https://xtermjs.org/)

---

**Status**: Ready for implementation
**Last Updated**: 2025-11-08
**Contact**: Development Team
