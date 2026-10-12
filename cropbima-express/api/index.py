"""Vercel serverless handler (python runtime). Keeps /tmp uploads + lazy DB init."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.main import app  # noqa: E402

# Vercel python runtime looks for `app` (or `handler`). Export both.
handler = app
