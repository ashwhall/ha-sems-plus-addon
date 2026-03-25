"""Load add-on configuration from /data/options.json."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

OPTIONS_PATH = Path("/data/options.json")
DEV_OPTIONS_PATH = Path(__file__).parent.parent / "dev_options.json"


@dataclass(frozen=True)
class AddonConfig:
    sems_username: str
    sems_password: str
    poll_interval_seconds: int = 300
    plant_id: str = ""

    def __post_init__(self) -> None:
        if not self.sems_username or not self.sems_password:
            raise ValueError("sems_username and sems_password are required")

    def __repr__(self) -> str:
        """Never expose credentials in logs."""
        return (
            f"AddonConfig(sems_username='***', sems_password='***', "
            f"poll_interval_seconds={self.poll_interval_seconds}, "
            f"plant_id={'***' if self.plant_id else ''})"
        )


def load_config() -> AddonConfig:
    """Read HA add-on options and return typed config."""
    if OPTIONS_PATH.exists():
        path = OPTIONS_PATH
    elif DEV_OPTIONS_PATH.exists():
        path = DEV_OPTIONS_PATH
    else:
        raise FileNotFoundError(
            f"Options file not found at {OPTIONS_PATH} or {DEV_OPTIONS_PATH}. "
            "Are you running inside the HA add-on environment, or do you have a dev_options.json?"
        )

    raw = json.loads(path.read_text(encoding="utf-8"))
    logger.info("Loaded add-on config: poll_interval=%ds", raw.get("poll_interval_seconds", 300))
    return AddonConfig(
        sems_username=raw["sems_username"],
        sems_password=raw["sems_password"],
        poll_interval_seconds=raw.get("poll_interval_seconds", 300),
        plant_id=raw.get("plant_id", ""),
    )
