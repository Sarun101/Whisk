import hashlib
import os


def hash_password(password: str, salt: str = None) -> str:
    """Hash a password with a random salt (or a given salt for verification)."""
    if salt is None:
        salt = os.urandom(16).hex()
    pwd_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${pwd_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Check a plain password against a stored 'salt$hash' string."""
    try:
        salt, pwd_hash = stored_hash.split("$")
    except ValueError:
        return False
    return hashlib.sha256((salt + password).encode()).hexdigest() == pwd_hash

