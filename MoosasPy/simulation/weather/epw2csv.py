"""Command-line entry point for EPW-to-DeST CSV conversion."""

from .epw import main


if __name__ == "__main__":
    raise SystemExit(main())