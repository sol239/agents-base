import argparse
from pathlib import Path
import shlex
import subprocess
import urllib.request
import urllib.error

from agent_config import container_name
from check_auth import check_auth_codex, check_auth_antigravity


parser = argparse.ArgumentParser(
    description="Checks status of the agents."
)

parser.add_argument(
    "-a",
    "--agent",
    type=str,
    choices=["codex", "cd", "antigravity", "ag", "ollama", "ol"],
    required=False,
    help="The name of the agent to get the status of",
)

AGENTS = {
    "codex": "codex",
    "cd": "codex",
    "antigravity": "antigravity",
    "ag": "antigravity",
    "ollama": "ollama",
    "ol": "ollama",
}


def is_running(agent: str) -> bool:
    if agent == "ollama":
        try:
            with urllib.request.urlopen(
                "http://localhost:11434/api/version",
                timeout=2,
            ) as response:
                return response.status == 200
        except (urllib.error.URLError, TimeoutError, OSError):
            return False

    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Running}}", container_name(agent)],
        capture_output=True,
        text=True,
        check=False,
    )

    return result.returncode == 0 and result.stdout.strip() == "true"


def get_auth_status(agent: str) -> str:
    authenticated = {
        "codex": check_auth_codex,
        "antigravity": check_auth_antigravity,
    }[agent]()
    return "AUTHENTICATED" if authenticated else "NOT AUTHENTICATED"


def print_status(agent: str) -> None:
    running = is_running(agent)

    print(f"{agent.capitalize()} is {'UP' if running else 'DOWN'}")

    if agent in ("codex", "antigravity"):
        auth = get_auth_status(agent) if running else "N/A"
        if auth == "NOT AUTHENTICATED":
            script = Path(__file__).resolve().with_name(f"auth_{agent}.py")
            auth += f" (python3 {shlex.quote(str(script))})"
        print(f"- Auth: {auth}")


def main() -> None:
    args = parser.parse_args()
    if args.agent:
        print_status(AGENTS[args.agent])
    else:
        for agent in ("codex", "antigravity", "ollama"):
            print_status(agent)
            print()


if __name__ == "__main__":
    main()
