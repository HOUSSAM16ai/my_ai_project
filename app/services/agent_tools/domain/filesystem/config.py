"""
Configuration constants for file system operations.
"""

MAX_READ_BYTES: int = 100_000
MAX_WRITE_BYTES: int = 5_000_000
MAX_APPEND_BYTES: int = 100_000
ENFORCE_APPEND_TOTAL: bool = True
AUTO_CREATE_ENABLED: bool = True
AUTO_CREATE_MAX_BYTES: int = 20_000
AUTO_CREATE_DEFAULT_CONTENT: str = ""
# If empty/None, all extensions allowed (unless blacklisted elsewhere).
# If set, only these are allowed for auto-creation.
AUTO_CREATE_ALLOWED_EXTS: list[str] | None = [
    ".txt", ".md", ".json", ".py", ".js", ".ts", ".html", ".css", ".csv", ".yml", ".yaml", ".sh"
]
