#!/usr/bin/env python3
"""Remove the folder thumbnails created by apply-folder-chooser-icons.py."""

from __future__ import annotations

import folder_chooser_icons as icons


if __name__ == "__main__":
    icons.restore()
