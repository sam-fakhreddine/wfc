# DevContainer

WFC ships a batteries-included devcontainer for end users. Drop `.devcontainer/`
into any project for a full secure development environment with WFC pre-installed.

---

## What's Included

### Languages and Runtimes

- **Python 3.12** with UV, black, ruff, pytest, mypy, pre-commit
- **Node.js LTS** with pnpm, bun, TypeScript, Vite, ESLint, Prettier, Tailwind CSS

### AI and Dev Tools

- **Claude Code CLI** — the WFC host
- **Kiro CLI** — Amazon's agentic IDE CLI
- **OpenCode CLI** — open-source AI coding assistant
- **GitHub CLI** (`gh`) — required for the WFC PR workflow
- **Docker-in-Docker** — docker-ce-cli, docker-compose-plugin

### Shell and Utilities

- ripgrep, fd, fzf, bat, exa, tmux, htop
- Oh My Zsh + Starship prompt

### Database Clients

- postgresql-client, redis-tools

### WFC Skills

All 30 WFC skills are auto-installed during container startup via
`install-universal.sh`. No manual setup needed.

---

## Setup Options

### Option A: Interactive (Guided)

```bash
bash .devcontainer/setup.sh
```

Walks you through prerequisites and starts the container.

### Option B: VS Code (Recommended)

1. Copy `.devcontainer/` into your project root
2. Copy the example env file and fill in your token:

   ```bash
   cp .devcontainer/.env.example .devcontainer/.env
   # Edit .env and set ANTHROPIC_AUTH_TOKEN
   ```

3. Open the project in VS Code
4. Press F1 and select "Dev Containers: Reopen in Container"

VS Code downloads the image, runs `postCreateCommand`, and opens an integrated
terminal inside the container.

### Option C: Docker CLI

```bash
cd .devcontainer
docker compose build
docker compose up -d
```

Then attach to the container with `docker exec -it <name> zsh`.

---

## Workspace Layout

```
/workspace/
├── app/        # Your project (mounted from host)
├── repos/
│   └── wfc/    # WFC framework (auto-cloned on first start)
└── tmp/        # Persistent scratch space
```

`/workspace/app` is a bind-mount of your host project directory. Changes you make
inside the container are immediately visible on your host and vice versa.

`/workspace/repos/wfc` is cloned automatically on first start. WFC skills are
installed from this clone.

---

## Firewall

The devcontainer includes an iptables-based firewall controlled by the
`FIREWALL_MODE` environment variable in `.devcontainer/.env`.

### Modes

| Mode | Behavior |
|------|----------|
| `audit` (default) | Logs all outbound traffic; nothing is blocked |
| `enforce` | Blocks traffic to non-whitelisted domains |

### Viewing Audit Logs

```bash
sudo tail -f /var/log/kern.log | grep FW-AUDIT
```

Each log line includes the destination IP and port. Use audit mode to discover
which domains your tools contact before switching to enforce mode.

### Whitelisting Domains (enforce mode)

Add entries to `.devcontainer/firewall-allowlist.txt` and restart the container.
The firewall reads the allowlist at startup.

---

## VS Code Extensions

The devcontainer installs these extensions automatically:

- **Python** — language support, IntelliSense
- **Ruff** — fast Python linter (replaces flake8)
- **Black** — Python formatter
- **ESLint** — JavaScript/TypeScript linting
- **Prettier** — multi-language formatter
- **Docker** — container management in the sidebar
- **GitHub Copilot** — AI code completion
- **GitLens** — enhanced Git history and blame

---

## After Starting

Once inside the container, verify WFC is ready:

```bash
wfc validate          # Confirm all 30 skills pass Agent Skills compliance
claude --version      # Confirm Claude Code CLI is installed
gh auth status        # Confirm GitHub CLI is authenticated
```

If `gh` is not authenticated, run `gh auth login` and follow the prompts.
