import os

os.environ.setdefault(
    "DATAINSIGHT_JWT_SECRET_KEY",
    "test-only-secret-key-with-at-least-32-characters",
)
os.environ.setdefault("DATAINSIGHT_AUTO_CREATE_TABLES", "false")
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
