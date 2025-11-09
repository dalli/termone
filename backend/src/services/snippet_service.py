"""Snippet service for managing SSH command snippets.

Provides:
- Create, read, update, delete snippets
- Execute snippets in terminal sessions
- Broadcast snippets to multiple sessions
- Search and filter snippets
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.schemas.snippets import (
    SnippetCreate,
    SnippetUpdate,
    SnippetResponse,
    SnippetExecuteRequest,
    SnippetBroadcastRequest,
)


class SnippetInfo:
    """In-memory snippet information storage."""

    def __init__(self, snippet_id: str, user_id: str, create_data: SnippetCreate):
        self.id = snippet_id
        self.user_id = user_id
        self.name = create_data.name
        self.description = create_data.description
        self.command = create_data.command
        self.tags = create_data.tags or []
        self.public = create_data.public or False
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        self.usage_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "command": self.command,
            "tags": self.tags,
            "public": self.public,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "usage_count": self.usage_count,
        }


class SnippetService:
    """High-level snippet management service."""

    def __init__(self):
        """Initialize snippet service."""
        self.snippets: Dict[str, SnippetInfo] = {}
        self.user_snippets: Dict[str, List[str]] = {}  # user_id -> [snippet_ids]
        self.executions: Dict[str, Dict[str, Any]] = {}  # execution_id -> execution_info

    async def create_snippet(
        self,
        user_id: str,
        create_data: SnippetCreate,
    ) -> SnippetResponse:
        """Create new snippet.

        Args:
            user_id: User ID
            create_data: Snippet creation data

        Returns:
            SnippetResponse
        """
        snippet_id = str(uuid.uuid4())
        snippet = SnippetInfo(snippet_id, user_id, create_data)

        # Store snippet
        self.snippets[snippet_id] = snippet
        if user_id not in self.user_snippets:
            self.user_snippets[user_id] = []
        self.user_snippets[user_id].append(snippet_id)

        return SnippetResponse(**snippet.to_dict())

    async def get_snippet(
        self,
        user_id: str,
        snippet_id: str,
    ) -> Optional[SnippetResponse]:
        """Get snippet by ID.

        Args:
            user_id: User ID
            snippet_id: Snippet ID

        Returns:
            SnippetResponse or None if not found
        """
        snippet = self.snippets.get(snippet_id)
        if not snippet:
            return None

        # Verify ownership or public access
        if snippet.user_id != user_id and not snippet.public:
            return None

        return SnippetResponse(**snippet.to_dict())

    async def list_snippets(
        self,
        user_id: str,
        tags: Optional[List[str]] = None,
        public_only: bool = False,
    ) -> List[SnippetResponse]:
        """List snippets for user.

        Args:
            user_id: User ID
            tags: Optional tag filter
            public_only: Only return public snippets

        Returns:
            List of SnippetResponse
        """
        snippets = []

        for snippet in self.snippets.values():
            # Check ownership/access
            if public_only:
                if not snippet.public:
                    continue
            else:
                if snippet.user_id != user_id and not snippet.public:
                    continue

            # Filter by tags
            if tags:
                if not any(tag in snippet.tags for tag in tags):
                    continue

            snippets.append(SnippetResponse(**snippet.to_dict()))

        return snippets

    async def update_snippet(
        self,
        user_id: str,
        snippet_id: str,
        update_data: SnippetUpdate,
    ) -> SnippetResponse:
        """Update snippet.

        Args:
            user_id: User ID
            snippet_id: Snippet ID
            update_data: Update data

        Returns:
            Updated SnippetResponse
        """
        snippet = self.snippets.get(snippet_id)
        if not snippet:
            raise ValueError("Snippet not found")

        # Verify ownership
        if snippet.user_id != user_id:
            raise ValueError("Access denied")

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(snippet, key, value)

        snippet.updated_at = datetime.utcnow().isoformat()

        return SnippetResponse(**snippet.to_dict())

    async def delete_snippet(
        self,
        user_id: str,
        snippet_id: str,
    ) -> bool:
        """Delete snippet.

        Args:
            user_id: User ID
            snippet_id: Snippet ID

        Returns:
            True if deleted, False if not found
        """
        snippet = self.snippets.get(snippet_id)
        if not snippet:
            return False

        # Verify ownership
        if snippet.user_id != user_id:
            return False

        # Remove from storage
        del self.snippets[snippet_id]
        if user_id in self.user_snippets:
            self.user_snippets[user_id].remove(snippet_id)
            if not self.user_snippets[user_id]:
                del self.user_snippets[user_id]

        return True

    async def execute_snippet(
        self,
        user_id: str,
        snippet_id: str,
        request: SnippetExecuteRequest,
    ) -> Dict[str, Any]:
        """Execute snippet in terminal session.

        Args:
            user_id: User ID
            snippet_id: Snippet ID
            request: Execution request

        Returns:
            Execution result
        """
        snippet = self.snippets.get(snippet_id)
        if not snippet:
            raise ValueError("Snippet not found")

        # Verify access
        if snippet.user_id != user_id and not snippet.public:
            raise ValueError("Access denied")

        # Create execution record
        execution_id = str(uuid.uuid4())
        execution_info = {
            "execution_id": execution_id,
            "snippet_id": snippet_id,
            "user_id": user_id,
            "session_id": request.session_id,
            "target_host_id": request.target_host_id,
            "status": "pending",
            "started_at": datetime.utcnow().isoformat(),
        }

        self.executions[execution_id] = execution_info

        # Increment usage count
        snippet.usage_count += 1

        return execution_info

    async def broadcast_snippet(
        self,
        user_id: str,
        snippet_id: str,
        request: SnippetBroadcastRequest,
    ) -> Dict[str, Any]:
        """Broadcast snippet to multiple terminal sessions.

        Args:
            user_id: User ID
            snippet_id: Snippet ID
            request: Broadcast request

        Returns:
            Broadcast result
        """
        snippet = self.snippets.get(snippet_id)
        if not snippet:
            raise ValueError("Snippet not found")

        # Verify access
        if snippet.user_id != user_id and not snippet.public:
            raise ValueError("Access denied")

        # Create broadcast record
        broadcast_id = str(uuid.uuid4())
        broadcast_info = {
            "broadcast_id": broadcast_id,
            "snippet_id": snippet_id,
            "user_id": user_id,
            "sessions": request.session_ids,
            "target_host_id": request.target_host_id,
            "status": "pending",
            "started_at": datetime.utcnow().isoformat(),
            "results": [],
        }

        # Increment usage count
        snippet.usage_count += 1

        return broadcast_info

    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status.

        Args:
            execution_id: Execution ID

        Returns:
            Execution info or None
        """
        return self.executions.get(execution_id)

    async def get_user_snippets_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for user's snippets.

        Args:
            user_id: User ID

        Returns:
            Statistics dictionary
        """
        snippet_ids = self.user_snippets.get(user_id, [])
        snippets = [self.snippets[sid] for sid in snippet_ids if sid in self.snippets]

        total_usage = sum(s.usage_count for s in snippets)
        all_tags = set()
        for snippet in snippets:
            all_tags.update(snippet.tags)

        return {
            "total_snippets": len(snippets),
            "total_usage": total_usage,
            "average_usage": total_usage / len(snippets) if snippets else 0,
            "available_tags": sorted(list(all_tags)),
        }
