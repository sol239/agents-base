"""Open Antigravity's interactive sign-in flow inside its Docker container."""

import subprocess
import sys

from agent_config import container_name


def main() -> int:
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        print("Run this script in an interactive terminal to sign in.", file=sys.stderr)
        return 1
    try:
        return subprocess.run(
            ["docker", "exec", "-it", container_name("antigravity"), "agy"],
            check=False,
        ).returncode
    except (OSError, ValueError) as error:
        print(f"Cannot start Antigravity login: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
