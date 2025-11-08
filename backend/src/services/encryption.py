"""Encryption service for securing sensitive data."""

import base64
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import os

from src.config import get_settings
from src.exceptions import EncryptionException

settings = get_settings()


class EncryptionService:
    """Service for AES-256-GCM encryption/decryption."""

    def __init__(self):
        """Initialize with master key from settings."""
        try:
            # Try to decode as base64 first
            if isinstance(settings.ENCRYPTION_MASTER_KEY, str):
                self.master_key = base64.b64decode(settings.ENCRYPTION_MASTER_KEY)
            else:
                self.master_key = settings.ENCRYPTION_MASTER_KEY

            # Ensure key is 32 bytes (256 bits)
            if len(self.master_key) < 32:
                # Pad with PBKDF2 if too short
                kdf = PBKDF2(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b"termone_salt",
                    iterations=100000,
                )
                self.master_key = kdf.derive(self.master_key)
            elif len(self.master_key) > 32:
                self.master_key = self.master_key[:32]
        except Exception as e:
            raise EncryptionException(f"Failed to initialize encryption key: {str(e)}")

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext using AES-256-GCM.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string with nonce and tag

        Raises:
            EncryptionException: If encryption fails
        """
        try:
            # Generate random nonce (96-bit for GCM)
            nonce = os.urandom(12)

            # Create cipher
            cipher = AESGCM(self.master_key)

            # Encrypt
            ciphertext = cipher.encrypt(nonce, plaintext.encode(), None)

            # Combine nonce + ciphertext and encode to base64
            encrypted = nonce + ciphertext
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            raise EncryptionException(f"Encryption failed: {str(e)}")

    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt AES-256-GCM encrypted string.

        Args:
            encrypted: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            EncryptionException: If decryption fails
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted)

            # Extract nonce (first 12 bytes) and ciphertext (rest)
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]

            # Create cipher and decrypt
            cipher = AESGCM(self.master_key)
            plaintext = cipher.decrypt(nonce, ciphertext, None)

            return plaintext.decode()
        except Exception as e:
            raise EncryptionException(f"Decryption failed: {str(e)}")


# Global instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get or create encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
