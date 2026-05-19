"""Static HTML documentation builder for Python projects."""

from __future__ import annotations

from .builder import build
from .config import BuildConfig

__all__ = ["BuildConfig", "build"]
