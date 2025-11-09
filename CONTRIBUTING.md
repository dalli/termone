# Contributing to Termone

Thank you for your interest in contributing to Termone! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please be respectful, inclusive, and professional in all interactions with other contributors and maintainers.

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Git
- SSH client

### Development Setup

1. **Fork the Repository**
   ```bash
   git clone https://github.com/yourusername/termone.git
   cd termone
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your local configuration
   alembic upgrade head
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   cp .env.example .env
   # Edit .env with your local API endpoint
   ```

4. **Start Development Servers**
   ```bash
   # Terminal 1: Backend
   cd backend
   source venv/bin/activate
   uvicorn src.main:app --reload

   # Terminal 2: Frontend
   cd frontend
   npm run dev
   ```

## Development Workflow

### Branch Naming Conventions

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

### Commit Message Format

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Test additions/changes
- `chore`: Build, dependencies, etc.

**Examples:**
```
feat(terminal): add command history persistence

Add ability to save and retrieve terminal command history
across sessions for better user experience.

Closes #123
```

```
fix(files): correct SFTP directory listing error

Fix issue where directory listing would fail with
special characters in filenames.

Closes #456
```

### Code Review Process

1. Create a feature branch from `main`
2. Make your changes with clear, focused commits
3. Push to your fork
4. Create a pull request with detailed description
5. Address review feedback
6. Merge once approved by maintainers

## Coding Standards

### Backend (Python)

**Style Guide:**
- Follow PEP 8 guidelines
- Use Black formatter: `black src/`
- Sort imports with isort: `isort src/`
- Max line length: 88 characters

**Type Hints:**
```python
# Always include type hints
async def list_hosts(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
) -> HostListResponse:
    """List hosts with pagination."""
    pass
```

**Documentation:**
```python
def create_host(host_data: HostCreate) -> Host:
    """Create a new SSH host.

    Args:
        host_data: Host configuration data

    Returns:
        Created host with ID and metadata

    Raises:
        DuplicateHostError: If host already exists
        InvalidCredentialsError: If credentials are invalid
    """
    pass
```

**Testing:**
```bash
# Run tests
cd backend
pytest tests/ -v

# Run specific test
pytest tests/contract/test_hosts.py::TestHostCreation -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Frontend (TypeScript/React)

**Style Guide:**
- Follow ESLint configuration
- Use Prettier: `npm run format`
- Max line length: 100 characters
- Use functional components with hooks

**Type Safety:**
```typescript
interface HostListProps {
  hosts: Host[];
  isLoading: boolean;
  onSelect: (hostId: string) => void;
}

export const HostList: React.FC<HostListProps> = ({
  hosts,
  isLoading,
  onSelect,
}) => {
  // Component implementation
};
```

**Testing:**
```bash
# Run tests
cd frontend
npm run test

# Run specific test file
npm run test -- HostList.test.tsx

# Run with coverage
npm run test:coverage
```

## Testing Requirements

### Backend Tests

**Contract Tests** (verify API contracts):
- Test endpoint request/response formats
- Verify status codes
- Test input validation
- Test authentication requirements

**Integration Tests** (verify workflows):
- Test multi-step operations
- Test permission boundaries
- Test state transitions
- Test error handling

**Test Structure:**
```python
class TestHostCreation:
    """Test host creation endpoint."""

    def test_create_host_with_valid_data(self, client: TestClient, auth_token: str):
        """Verify host creation with valid configuration."""
        response = client.post(
            "/api/hosts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "prod-server",
                "hostname": "prod.example.com",
                "port": 22,
                "username": "ubuntu",
                "auth_type": "password",
                "password": "secure-password",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "prod-server"
        assert "id" in data
```

### Frontend Tests

- Component rendering tests
- User interaction tests
- Hook tests
- API integration tests

**Test Coverage Targets:**
- Backend: ≥80% for security-critical paths
- Frontend: ≥70% for critical components

## Documentation

### Code Documentation
- Document all public functions/classes with docstrings
- Include parameter types and return types
- Explain complex logic with comments
- Keep documentation up-to-date

### API Documentation
- Document all endpoints in code
- Include request/response examples
- Document authentication requirements
- Document error responses

### User Documentation
- Update README.md for feature changes
- Create/update guides in `docs/` directory
- Include screenshots for UI changes
- Document configuration options

## Performance Considerations

### Backend
- Use async/await for I/O operations
- Cache database queries when appropriate
- Implement pagination for large result sets
- Monitor query performance with logging

### Frontend
- Code split for better load times
- Lazy load components
- Memoize expensive computations
- Optimize re-renders with useMemo/useCallback

## Security Checklist

Before submitting a pull request:

- [ ] Input validation for all endpoints
- [ ] Authentication/authorization checks
- [ ] SQL injection prevention (ORM usage)
- [ ] XSS prevention (React escaping)
- [ ] CSRF protection if applicable
- [ ] No hardcoded secrets/credentials
- [ ] No sensitive data in logs
- [ ] Proper error messages (no information leakage)
- [ ] Rate limiting considered
- [ ] Encryption for sensitive data

## Pull Request Process

1. **Title**: Use clear, descriptive title following commit message format
2. **Description**: Include:
   - What problem does this solve?
   - How does it solve it?
   - What changes were made?
   - Testing performed
   - Screenshots (for UI changes)
   - Related issues/PRs

3. **Example PR Description**:
   ```markdown
   ## Description
   Add terminal session history persistence to allow users to
   review and replay previous commands.

   ## Changes
   - Add command history table to database schema
   - Implement TerminalService.get_history() method
   - Add `/terminal/history` endpoint
   - Create TerminalHistory React component

   ## Testing
   - ✅ Contract tests: all passing
   - ✅ Integration tests: all passing
   - ✅ Manual testing: verified history persistence

   ## Screenshots
   [If applicable, add screenshots]

   Closes #789
   ```

4. **Checklist**:
   - [ ] Tests pass locally
   - [ ] Code follows style guidelines
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)
   - [ ] Commits are clear and focused

## Release Process

### Versioning

Termone follows Semantic Versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Release Steps

1. Update version in `package.json` and `pyproject.toml`
2. Update CHANGELOG.md with release notes
3. Create release commit: `chore(release): v0.x.y`
4. Create git tag: `v0.x.y`
5. Create GitHub release with notes
6. Publish packages

## Reporting Issues

### Bug Reports

Include:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Environment info (OS, Python/Node version)
- Logs/error messages
- Screenshots (if applicable)

### Feature Requests

Include:
- Clear description of desired feature
- Use case and motivation
- Proposed implementation (if any)
- Related features/systems

## Becoming a Maintainer

Active contributors with high-quality work may be invited to join the maintainer team. This includes:
- Code review rights
- Merge permissions
- Release management
- Community support

## License

By contributing to Termone, you agree that your contributions will be licensed under the MIT License.

## Questions?

- 📖 Check existing issues and PRs
- 📧 Email: dev@termone.dev
- 💬 GitHub Discussions: Ask in the community
- 📚 Documentation: Check docs/ directory

---

Thank you for contributing to Termone! 🎉
