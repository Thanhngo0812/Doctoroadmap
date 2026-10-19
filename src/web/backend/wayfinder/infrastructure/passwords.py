"""Argon2id passwords and the offline, versioned common-password blocklist."""
from importlib.resources import files
import secrets

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._hasher = PasswordHasher(time_cost=2, memory_cost=19 * 1024, parallelism=1,
                                      hash_len=32, salt_len=16, type=Type.ID)
        self.dummy_hash = self.hash(secrets.token_urlsafe(32))

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, encoded: str, password: str) -> bool:
        try:
            return self._hasher.verify(encoded, password)
        except (InvalidHashError, VerificationError):
            return False


def load_common_passwords() -> frozenset[str]:
    content = files("wayfinder").joinpath("data/common_passwords.txt").read_text(encoding="utf-8")
    return frozenset(line.strip().casefold() for line in content.splitlines() if line.strip())
