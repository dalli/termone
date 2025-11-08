"""Credential management service."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.infrastructure import Credential
from src.services.encryption import EncryptionService
from src.exceptions import ValidationException, NotFoundException


class CredentialService:
    """Service for managing SSH credentials with encryption."""

    def __init__(self, encryption_service: EncryptionService):
        """Initialize credential service."""
        self.encryption_service = encryption_service

    async def create_credential(
        self,
        db: AsyncSession,
        host_id: str,
        credential_type: str,
        value: str,
    ) -> Credential:
        """
        Create and encrypt a new credential.

        Args:
            db: Database session
            host_id: Host ID this credential belongs to
            credential_type: Type of credential (password, ssh_key, etc.)
            value: Plaintext credential value to encrypt

        Returns:
            Credential object

        Raises:
            ValidationException: If credential type is invalid
        """
        if not value or len(value.strip()) == 0:
            raise ValidationException(
                field="value",
                message="Credential value cannot be empty",
                code="EMPTY_CREDENTIAL",
            )

        if credential_type not in ["password", "ssh_key"]:
            raise ValidationException(
                field="credential_type",
                message=f"Invalid credential type: {credential_type}",
                code="INVALID_CREDENTIAL_TYPE",
            )

        # Encrypt the credential value
        encrypted_value = self.encryption_service.encrypt(value)

        credential = Credential(
            host_id=host_id,
            credential_type=credential_type,
            encrypted_value=encrypted_value,
        )

        db.add(credential)
        await db.commit()
        await db.refresh(credential)

        return credential

    async def get_credential(
        self,
        db: AsyncSession,
        credential_id: str,
    ) -> Optional[Credential]:
        """
        Retrieve a credential by ID.

        Args:
            db: Database session
            credential_id: Credential ID

        Returns:
            Credential object or None

        Raises:
            NotFoundException: If credential not found
        """
        result = await db.execute(
            select(Credential).where(Credential.id == credential_id)
        )
        credential = result.scalar_one_or_none()

        if not credential:
            raise NotFoundException(
                resource="Credential",
                identifier=credential_id,
            )

        return credential

    async def get_host_credential(
        self,
        db: AsyncSession,
        host_id: str,
    ) -> Optional[Credential]:
        """
        Get the credential for a specific host.

        Args:
            db: Database session
            host_id: Host ID

        Returns:
            Credential object or None if not found
        """
        result = await db.execute(
            select(Credential).where(Credential.host_id == host_id)
        )
        return result.scalar_one_or_none()

    async def decrypt_credential(
        self,
        credential: Credential,
    ) -> str:
        """
        Decrypt a credential value.

        Args:
            credential: Credential object

        Returns:
            Decrypted credential value
        """
        return self.encryption_service.decrypt(credential.encrypted_value)

    async def update_credential(
        self,
        db: AsyncSession,
        credential_id: str,
        value: str,
        credential_type: Optional[str] = None,
    ) -> Credential:
        """
        Update a credential with new encrypted value.

        Args:
            db: Database session
            credential_id: Credential ID
            value: New plaintext value
            credential_type: Optional new credential type

        Returns:
            Updated Credential object

        Raises:
            ValidationException: If value is invalid
            NotFoundException: If credential not found
        """
        if not value or len(value.strip()) == 0:
            raise ValidationException(
                field="value",
                message="Credential value cannot be empty",
                code="EMPTY_CREDENTIAL",
            )

        credential = await self.get_credential(db, credential_id)

        # Encrypt new value
        credential.encrypted_value = self.encryption_service.encrypt(value)

        if credential_type:
            if credential_type not in ["password", "ssh_key"]:
                raise ValidationException(
                    field="credential_type",
                    message=f"Invalid credential type: {credential_type}",
                    code="INVALID_CREDENTIAL_TYPE",
                )
            credential.credential_type = credential_type

        db.add(credential)
        await db.commit()
        await db.refresh(credential)

        return credential

    async def delete_credential(
        self,
        db: AsyncSession,
        credential_id: str,
    ) -> bool:
        """
        Delete a credential.

        Args:
            db: Database session
            credential_id: Credential ID

        Returns:
            True if deleted successfully

        Raises:
            NotFoundException: If credential not found
        """
        credential = await self.get_credential(db, credential_id)

        await db.delete(credential)
        await db.commit()

        return True

    async def delete_host_credentials(
        self,
        db: AsyncSession,
        host_id: str,
    ) -> int:
        """
        Delete all credentials for a host.

        Args:
            db: Database session
            host_id: Host ID

        Returns:
            Number of credentials deleted
        """
        result = await db.execute(
            select(Credential).where(Credential.host_id == host_id)
        )
        credentials = result.scalars().all()

        for credential in credentials:
            await db.delete(credential)

        await db.commit()

        return len(credentials)

    async def rotate_credential(
        self,
        db: AsyncSession,
        credential_id: str,
        new_value: str,
    ) -> Credential:
        """
        Rotate (update) a credential with a new value.

        Args:
            db: Database session
            credential_id: Credential ID
            new_value: New plaintext value

        Returns:
            Updated Credential object
        """
        return await self.update_credential(db, credential_id, new_value)
