import subprocess

from agent_config import container_name


def check_auth_codex() -> bool:
    """Return whether Codex reports a saved login in its container."""
    try:
        result = subprocess.run(
            ["docker", "exec", container_name("codex"), "codex", "login", "status"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=15,
            check=False,
        )
        return result.returncode == 0
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


def check_auth_antigravity() -> bool:
    """Return whether Antigravity can fetch its authenticated model list.

    Network failures also return False; no model prompt is submitted.
    """
    try:
        result = subprocess.run(
            ["docker", "exec", container_name("antigravity"), "agy", "models"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=15,
            check=False,
        )
        return result.returncode == 0
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False
