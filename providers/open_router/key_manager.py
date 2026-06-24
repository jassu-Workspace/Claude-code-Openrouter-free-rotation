"""OpenRouter key management and rotation."""

import logging
import threading
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("openrouter_rotation")
_log_file = Path("logs/openrouter_rotation.log")
_log_file.parent.mkdir(parents=True, exist_ok=True)
fh = logging.FileHandler(_log_file)
fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(fh)
logger.setLevel(logging.INFO)


@dataclass
class KeyState:
    healthy: bool = True
    exhausted: bool = False
    last_error: str = ""


class OpenRouterKeyManager:
    def __init__(self, api_key: str = "", api_keys_file: str = ""):
        self.lock = threading.Lock()
        self.keys: list[str] = []
        self.key_states: dict[str, KeyState] = {}
        self.current_index: int = 0
        self.api_keys_file = api_keys_file

        if api_keys_file and Path(api_keys_file).is_file():
            self.reload_keys()
        elif api_key:
            for key in api_key.splitlines():
                k = key.strip()
                if k and not k.startswith("#"):
                    self._add_key(k)
                    logger.info("Key loaded")

    def _add_key(self, key: str):
        if key not in self.key_states:
            self.keys.append(key)
            self.key_states[key] = KeyState()

    def reload_keys(self) -> None:
        with self.lock:
            if not self.api_keys_file or not Path(self.api_keys_file).is_file():
                return

            try:
                with open(self.api_keys_file, encoding="utf-8") as f:
                    lines = f.readlines()

                new_keys = []
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    new_keys.append(line)
                    if line not in self.key_states:
                        self.key_states[line] = KeyState()
                        logger.info("Key loaded")

                self.keys = new_keys
                if self.current_index >= len(self.keys):
                    self.current_index = 0
            except Exception as e:
                logger.error(f"Error reloading keys: {e}")

    def get_current_key(self) -> str:
        with self.lock:
            if not self.keys:
                return ""
            return self.keys[self.current_index]

    def rotate_key(self, error_message: str = "") -> None:
        with self.lock:
            if not self.keys:
                return

            current_key = self.keys[self.current_index]
            self.key_states[current_key].healthy = False
            self.key_states[current_key].last_error = error_message

            start_index = self.current_index
            while True:
                self.current_index = (self.current_index + 1) % len(self.keys)
                next_key = self.keys[self.current_index]
                if (
                    not self.key_states[next_key].exhausted
                    or self.current_index == start_index
                ):
                    break

            logger.info("Key rotated")

    def mark_key_exhausted(self, error_message: str = "") -> None:
        with self.lock:
            if not self.keys:
                return

            current_key = self.keys[self.current_index]
            self.key_states[current_key].healthy = False
            self.key_states[current_key].exhausted = True
            self.key_states[current_key].last_error = error_message
            logger.info("Key exhausted")

    def get_status(self) -> dict:
        with self.lock:
            healthy_count = sum(1 for k in self.keys if self.key_states[k].healthy)
            exhausted_count = sum(
                1 for k in self.keys if self.key_states[k].exhausted
            )
            return {
                "total_keys": len(self.keys),
                "healthy_keys": healthy_count,
                "exhausted_keys": exhausted_count,
                "current_key_index": self.current_index,
            }
