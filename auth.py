import hashlib
from typing import Optional, Tuple
from database import Database

class Auth:
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def authenticate(username: str, password: str) -> Optional[Tuple]:
        rows = Database.execute(
            "SELECT id, username, role FROM users WHERE username = ? AND password_hash = ?",
            (username, Auth.hash_password(password)),
            fetch=True,
        )
        return rows[0] if rows else None
