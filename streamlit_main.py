#!/usr/bin/env python3
"""
Entry point for Streamlit application
"""

import sys
from pathlib import Path

# Add src to Python path so we can import our modules
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the Streamlit app (after path is set)
from natural_shift_planner.streamlit_app import main


if __name__ == "__main__":
    main()
