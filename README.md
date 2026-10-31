# Agents Base

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![Ruff](https://img.shields.io/badge/Checks-Ruff-D7FF64)
![Pyright](https://img.shields.io/badge/Types-Pyright-blue)

A shared Python interface for Codex CLI, Antigravity CLI, and local Ollama, with notebook examples.

## Setup

Requires Python 3.12+, Docker Compose, and Node.js for Pyright.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt fastapi ipykernel
git config --local core.hooksPath .githooks
```

Create `.env` in the project root:

```dotenv
CODEX_CONTAINER_NAME=base-codex-container
ANTIGRAVITY_CONTAINER_NAME=base-antigravity-container
```

Start the containers and sign in:

```bash
docker compose up -d --build
docker compose exec codex codex login --device-auth
docker compose exec antigravity agy
docker compose exec ollama ollama pull llama3.2:3b
```

Complete Antigravity sign-in, then exit its interactive CLI. Authentication and Ollama models persist in Docker volumes.

## Notebooks

Open a notebook in VS Code, select the `.venv` Python kernel, and run cells in order:

- [Codex CLI](notebooks/codex_cli.ipynb)
- [Antigravity CLI](notebooks/antigravity_cli.ipynb)
- [Ollama](notebooks/ollama.ipynb)

The examples assume the kernel starts in `notebooks/`. CLI sessions use `/workspace`, mounted from the host's `./workspace` directory. Ollama currently supports chat without file-editing tools. Session state is stored in memory per provider instance.

## Checks

```bash
./scripts/check_lint.sh
./scripts/check_types.sh
./scripts/check_format.sh
```

The pre-push hook runs all three checks. If formatting fails, it applies formatting and blocks the push. Review and commit the changes, then push again.

GitHub Actions runs the same checks on pushes and pull requests, with a separate result for each check.

To format manually:

```bash
.venv/bin/ruff format .
```
