from pathlib import Path


def save_output_file(path: Path) -> Path:
    # Local mode: files are already written to OUTPUT_DIR.
    return path
