#!/usr/bin/env python3
"""
Terminedia Paint - ASCII Art Drawing Application
Run with: python terminedia-paint.py
"""

import sys
from pathlib import Path

# Add the current directory to Python path so we can import terminedia_paint
sys.path.insert(0, str(Path(__file__).parent))

import terminedia_paint

if __name__ == "__main__":
    terminedia_paint.run()
