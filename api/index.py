"""Vercel serverless entrypoint for the LeadGen Pro FastAPI API."""

from __future__ import annotations

import sys
from pathlib import Path

from mangum import Mangum

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import create_app  # noqa: E402

app = create_app()
handler = Mangum(app)
