#!/usr/bin/env python3
"""Remove the Chrome cursor exception created by apply-browser-cursors.py."""

from __future__ import annotations

import browser_cursors as cursors


if __name__ == "__main__":
    cursors.restore()
