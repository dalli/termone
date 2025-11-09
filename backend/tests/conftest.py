import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.database import get_db
from src.config import Settings


@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        DEBUG=False,
        TESTING=True,
    )
