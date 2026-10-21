import os
import argparse
from pathlib import Path
import shlex
import subprocess
import sys


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Sign in to Codex inside its container.")
    parser.add_argument(
        "--auth",
        choices=("web", "device"),
        default="web",
        help="Authentication flow to use (default: web)",
    )
    args = parser.parse_args()

    try:
        command = ["docker", "exec", "-i"]
        if sys.stdin.isatty() and sys.stdout.isatty():
            command.append("-t")
        command.extend([container_name("codex"), "codex", "login"])
        if args.auth == "device":
            command.append("--device-auth")
        return subprocess.run(command, check=False).returncode
    except (OSError, ValueError) as error:
        print(f"Cannot start Codex login: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())


