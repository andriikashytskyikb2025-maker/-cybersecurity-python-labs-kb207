from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import os
import re

PBKDF2_ITERATIONS = 100_000
SESSION_TIMEOUT_SEC = 900

EMAIL_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9._]{2,63}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class User:
    def __init__(self, username: str, email: str, role: str = "user", active: bool = True):
        self.username = username
        self.email = email
        self.role = role
        self.active = active
        self.__password_hash: bytes | None = None
        self.__password_salt: bytes | None = None

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str):
        if not EMAIL_REGEX.match(value):
            raise ValueError(f"Некоректний формат email: '{value}'")
        self._email = value

    def set_password(self, password: str) -> None:
        self.__password_salt = os.urandom(16)
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

    def check_password(self, password: str) -> bool:
        if not self.__password_hash or not self.__password_salt:
            return False
        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )
        return hmac.compare_digest(self.__password_hash, candidate_hash)

    def deactivate(self) -> None:
        self.active = False

    def __str__(self) -> str:
        status = "Active" if self.active else "Inactive"
        return f"User({self.username}, {self.email}, role={self.role}, status={status})"


class Admin(User):
    def __init__(self, username: str, email: str, permissions: set[str] | list[str] | None = None, active: bool = True):
        super().__init__(username, email, role="admin", active=active)
        self.permissions = set(permissions) if permissions is not None else set()

    def grant_permission(self, permission: str) -> None:
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __str__(self) -> str:
        base_str = super().__str__()
        perms_str = ", ".join(sorted(self.permissions)) if self.permissions else "None"
        return f"{base_str} [Permissions: {perms_str}]"


class Session:
    def __init__(self, ip: str):
        self.ip = ip
        now = datetime.now(timezone.utc)
        self.login_time: datetime = now
        self.last_activity: datetime = now

    def touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        if timeout_sec <= 0:
            raise ValueError("timeout_sec повинен бути додатним числом")
        now = datetime.now(timezone.utc)
        return (now - self.last_activity) < timedelta(seconds=timeout_sec)


@dataclass
class LogEntry:
    timestamp: datetime
    username: str
    action: str


class AuditLog:
    def __init__(self):
        self.logs: list[LogEntry] = []

    def add_log(self, username: str, action: str) -> None:
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc),
            username=username,
            action=action,
        )
        self.logs.append(entry)

    def show_all(self) -> list[str]:
        result = []
        for log in self.logs:
            time_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            result.append(f"[{time_str}] {log.username}: {log.action}")
        return result


class UserAccount:
    def __init__(self, user: User, session: Session | None = None, audit_log: AuditLog | None = None):
        self.user = user
        self.session = session
        self.audit_log = audit_log if audit_log is not None else AuditLog()

    def login(self, username: str, password: str, ip: str) -> bool:
        if self.user.username != username or not self.user.active:
            self.audit_log.add_log(username, "login_failure")
            return False

        if self.user.check_password(password):
            self.session = Session(ip=ip)
            self.session.touch()
            self.audit_log.add_log(username, "login_success")
            return True

        self.audit_log.add_log(username, "login_failure")
        return False

    def is_authenticated(self) -> bool:
        if self.session is None:
            return False
        return self.session.is_active(SESSION_TIMEOUT_SEC)

    def logout(self) -> None:
        if self.session:
            self.audit_log.add_log(self.user.username, "logout")
            self.session = None

    def __getitem__(self, item: str):
        allowed_keys = {
            "user": self.user,
            "session": self.session,
            "audit_log": self.audit_log,
            "username": self.user.username,
            "email": self.user.email,
            "role": self.user.role,
            "active": self.user.active,
        }
        if item in ("_User__password_hash", "_User__password_salt", "password", "hash", "salt"):
            raise KeyError("Доступ до хешу та солі пароля заборонено.")
        if item in allowed_keys:
            return allowed_keys[item]
        raise KeyError(f"Невідомий ключ: '{item}'")

    def __setitem__(self, key: str, value):
        if key in ("_User__password_hash", "_User__password_salt", "password", "hash", "salt"):
            raise KeyError("Доступ до хешу та солі пароля заборонено.")
        if key == "user":
            if not isinstance(value, User):
                raise TypeError("Значення для 'user' повинно бути екземпляром User")
            self.user = value
        elif key == "session":
            if value is not None and not isinstance(value, Session):
                raise TypeError("Значення для 'session' повинно бути екземпляром Session або None")
            self.session = value
        elif key == "audit_log":
            if not isinstance(value, AuditLog):
                raise TypeError("Значення для 'audit_log' повинно бути екземпляром AuditLog")
            self.audit_log = value
        elif key == "email":
            self.user.email = value
        elif key == "active":
            if not isinstance(value, bool):
                raise TypeError("Значення для 'active' повинно бути bool")
            self.user.active = value
        else:
            raise KeyError(f"Невідомий ключ для запису: '{key}'")