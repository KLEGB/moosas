from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    ROOT_DIR: Path = Path(__file__).resolve().parents[2]
    INPUT_DIR: Path = ROOT_DIR / "runtime" / "input"
    OUTPUT_DIR: Path = ROOT_DIR / "runtime" / "output"
    EPW_FOLDER: Path = ROOT_DIR / "Global_EPW" / "epwFiles"


settings = Settings()
settings.INPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)