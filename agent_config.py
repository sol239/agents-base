import os
from pathlib import Path
import shlex


def container_name(agent: str) -> str:
    key = f"{agent.upper()}_CONTAINER_NAME"
    # Match Compose's precedence: shell environment overrides .env.
    value = os.environ.get(key)
    if value is None:
        env_path = Path(__file__).resolve().with_name(".env")
        for line in env_path.read_text().splitlines():
            name, separator, raw_value = line.partition("=")
            if separator and name.strip() == key:
                values = shlex.split(raw_value, comments=True)
                value = " ".join(values)
    if not value:
        raise ValueError(f"Set {key} in .env or the environment")
    return value


