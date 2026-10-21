"""Sign in to Codex inside its Docker container using a device code."""

import subprocess
import sys

from agent_config import container_name


def main() -> int:
    try:
        command = ["docker", "exec", "-i"]
        if sys.stdin.isatty() and sys.stdout.isatty():
            command.append("-t")
        command.extend([container_name("codex"), "codex", "login", "--device-auth"])
        return subprocess.run(command, check=False).returncode
    except (OSError, ValueError) as error:
        print(f"Cannot start Codex login: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
