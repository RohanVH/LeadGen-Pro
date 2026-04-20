import sys
from pathlib import Path
from typing import Callable, Awaitable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_PATH = PROJECT_ROOT / "backend"

if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.main import app as fastapi_app


class VercelAPIPrefixAdapter:
    """Strip the /api prefix so the same FastAPI routes work locally and on Vercel."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive: Callable[[], Awaitable[dict]], send) -> None:
        if scope["type"] in {"http", "websocket"}:
            path = scope.get("path", "")
            if path == "/api":
                scope = {**scope, "path": "/"}
            elif path.startswith("/api/"):
                scope = {**scope, "path": path[4:]}

        await self.app(scope, receive, send)


app = VercelAPIPrefixAdapter(fastapi_app)
