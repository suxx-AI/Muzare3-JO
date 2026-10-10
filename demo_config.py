"""One shared local-demo configuration for Django and the Windows launcher."""
import hashlib
import os
from uuid import uuid4
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DEMO_HOST = "127.0.0.1"
DEMO_PORT = 8765
PROJECT_ID = hashlib.sha256(os.path.normcase(str(PROJECT_ROOT)).encode()).hexdigest()[:24]
RUNTIME_DIR = PROJECT_ROOT / ".runtime"
BOOT_ID = str(uuid4())


def local_secret_key():
    """Create a persistent local Django key, never a hardcoded secret."""
    import secrets
    RUNTIME_DIR.mkdir(exist_ok=True)
    path = RUNTIME_DIR / "django-secret.key"
    try:
        with path.open("x", encoding="utf-8") as file:
            file.write(secrets.token_urlsafe(64))
    except FileExistsError:
        pass
    key = path.read_text(encoding="utf-8").strip()
    if not key:
        raise RuntimeError("The local Django secret-key file is empty")
    return key
