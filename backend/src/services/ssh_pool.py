"""SSH connection pool for managing SSH sessions."""

from typing import Dict, List
from datetime import datetime


class SSHConnectionPool:
    """Pool for managing SSH connections."""

    def __init__(self, max_connections: int = 50):
        self.max_connections = max_connections
        self.connections: Dict[str, Dict] = {}

    async def add_connection(self, session_id: str, connection_info: Dict):
        """Add SSH connection to pool."""
        if len(self.connections) >= self.max_connections:
            # Remove oldest inactive
            self._cleanup_inactive()
        
        self.connections[session_id] = {
            **connection_info,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        }

    def get_connection(self, session_id: str):
        """Get SSH connection from pool."""
        return self.connections.get(session_id)

    def remove_connection(self, session_id: str):
        """Remove SSH connection from pool."""
        self.connections.pop(session_id, None)

    def _cleanup_inactive(self):
        """Remove inactive connections."""
        if self.connections:
            # Simple cleanup: remove oldest
            oldest_key = min(
                self.connections.keys(),
                key=lambda k: self.connections[k]["last_activity"],
            )
            self.connections.pop(oldest_key)


def get_ssh_pool() -> SSHConnectionPool:
    """Get SSH connection pool instance."""
    return SSHConnectionPool()
