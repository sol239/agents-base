# Agents Base

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![Ruff](https://img.shields.io/badge/Checks-Ruff-D7FF64)
![Pyright](https://img.shields.io/badge/Types-Pyright-blue)

A shared Python interface for Codex CLI, Antigravity CLI, and local Ollama, with notebook examples.

## Setup (using in other apps/repos)

```bash
# In the other repository run:

# 1) add a git submodule (skip if already done)
git submodule add \
  https://github.com/sol239/agents-base.git \
  agents-base

# 2) update the submodule
git submodule update --init --recursive
```

Create `agents-base/.env` with the host repository's absolute path:

Choose your own container names; the names below are examples. Each name must be unique on your Docker host.

```dotenv
CODEX_CONTAINER_NAME=your-project-codex
ANTIGRAVITY_CONTAINER_NAME=your-project-antigravity
AGENT_WORKSPACE=/absolute/path/to/your-project
```

Start the CLI containers from the submodule directory:

```bash
cd agents-base
docker compose up -d --build codex antigravity
```

Both agents now see the entire host repository at `/workspace`. Create sessions with `workspace_id="/workspace"`. Follow the sign-in commands below if needed. No parent Compose file or microservice is required for this setup.

Both CLI agents discover project skills in `your-project/.agents/skills/<skill-name>/SKILL.md`, available inside the containers at `/workspace/.agents/skills/<skill-name>/SKILL.md`. Place shared project skills there, rather than in the `agents-base` submodule's `.agents` directory.

Changing `AGENT_WORKSPACE` requires running `docker compose up -d codex antigravity` again to recreate the containers with the new mount. The image does not need rebuilding. Without this variable, the mount defaults to `./workspace`.

## Setup (using on its own)

Requires Python 3.12+, Docker Compose, and Node.js for Pyright.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt fastapi ipykernel
git config --local core.hooksPath .githooks
```

Create `.env` in the project root:

```dotenv
CODEX_CONTAINER_NAME=your-project-codex
ANTIGRAVITY_CONTAINER_NAME=your-project-antigravity
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

The examples assume the kernel starts in `notebooks/`. CLI sessions use `/workspace`, mounted from `AGENT_WORKSPACE` or the host's `./workspace` directory by default. Ollama currently supports chat without file-editing tools. Session state is stored in memory per provider instance.

## Checks

```bash
# Ruff Linter
./scripts/check_lint.sh

# Pyright
./scripts/check_types.sh

# Ruff Formatter
./scripts/check_format.sh
```

The pre-push hook runs all three checks. If formatting fails, it applies formatting and blocks the push. Review and commit the changes, then push again.

GitHub Actions runs the same checks on pushes and pull requests, with a separate result for each check.

To format manually:

```bash
.venv/bin/ruff format .
```
