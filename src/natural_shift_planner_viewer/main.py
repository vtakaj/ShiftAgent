#!/usr/bin/env python3
"""
Entry point for Streamlit application
"""


def main():
    """Main entry point for Streamlit app"""
    # Import after path is set to avoid import errors
    from natural_shift_planner.streamlit_app import main as streamlit_main

    streamlit_main()


if __name__ == "__main__":
    main()
