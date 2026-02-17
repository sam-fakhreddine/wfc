# ═══════════════════════════════════════════════════════════════════════════════
# WFC DevContainer - Optimized Multi-Stage Build
#
# Layer Strategy (least → most volatile):
#   Stage 1 (base-system):   OS + ALL apt packages         — changes ~never
#   Stage 2 (python-runtime): Python + UV + global tools    — changes rarely
#   Stage 3 (node-runtime):   Node + pnpm/bun + globals     — changes rarely
#   Stage 4 (dev-tools):      Docker/gh/Kiro/Entire/OMZ     — changes occasionally
#   Stage 5 (devcontainer):   User config + WFC clone       — changes most often
#
# Optimizations:
#   - Single apt-get update per stage (was 4 separate calls)
#   - Consolidated RUN commands (~15 layers instead of ~30)
#   - BuildKit cache mounts for pip/uv/npm/pnpm
#   - Volatile steps (git clone, home config) pushed to final stage
# ═══════════════════════════════════════════════════════════════════════════════

# ────────────────────────────────────────────────────────────────────────────────
# STAGE 1: Base System — Ubuntu + ALL apt packages
# This is the heaviest layer but changes the least. Includes everything
# installable via apt so we never apt-get update again in later stages.
# ────────────────────────────────────────────────────────────────────────────────
FROM ubuntu:24.04 AS base-system

ENV DEBIAN_FRONTEND=noninteractive

# Create non-root user early (needed by later stages)
ARG USERNAME=wfc
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Single mega apt-get: core tools + dev tools + database clients + shell tools
# Ordering: build-essential → version-control → network → editors → shell → db → dev-utils
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    build-essential gcc g++ make cmake \
    # Version control + SSH
    git git-lfs openssh-client \
    # Network + download
    curl wget ca-certificates \
    # Firewall (CRITICAL for security model)
    iptables iproute2 \
    # System utilities
    sudo lsb-release gnupg2 software-properties-common \
    # Editors
    vim nano \
    # Shell + terminal tools
    zsh tmux jq tree htop \
    # Modern CLI replacements
    bat eza fd-find ripgrep fzf \
    # Network diagnostics
    net-tools iputils-ping dnsutils telnet netcat-openbsd \
    # Database clients
    postgresql-client redis-tools \
    # Antivirus
    clamav clamav-daemon clamav-freshclam \
    # Python alias (python → python3)
    python-is-python3 \
    # Misc (unzip needed by Kiro CLI, pgloader for DB migrations)
    unzip pgloader \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create user + git config + SSH known hosts (one layer)
RUN set -eux; \
    if getent group $USER_GID >/dev/null 2>&1; then \
        existing_group=$(getent group $USER_GID | cut -d: -f1); \
        if [ "$existing_group" != "$USERNAME" ]; then \
            groupmod --new-name $USERNAME $existing_group 2>/dev/null || \
            groupdel $existing_group 2>/dev/null || true && \
            groupadd --gid $USER_GID $USERNAME 2>/dev/null || true; \
        fi; \
    else \
        groupadd --gid $USER_GID $USERNAME 2>/dev/null || \
        groupadd $USERNAME; \
    fi; \
    if getent passwd $USER_UID >/dev/null 2>&1; then \
        existing_user=$(getent passwd $USER_UID | cut -d: -f1); \
        if [ "$existing_user" != "$USERNAME" ]; then \
            usermod --login $USERNAME --home /home/$USERNAME --move-home $existing_user 2>/dev/null || \
            (userdel $existing_user 2>/dev/null || true && \
            useradd --uid $USER_UID --gid $USER_GID -m $USERNAME); \
            usermod --gid $USER_GID $USERNAME 2>/dev/null || true; \
        fi; \
    elif id -u $USERNAME >/dev/null 2>&1; then \
        usermod --uid $USER_UID --gid $USER_GID $USERNAME 2>/dev/null || \
        (userdel $USERNAME 2>/dev/null || true && \
        useradd --uid $USER_UID --gid $USER_GID -m $USERNAME); \
    else \
        useradd --uid $USER_UID --gid $USER_GID -m $USERNAME; \
    fi; \
    echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME && \
    mkdir -p /home/$USERNAME/.local/bin && \
    mkdir -p /etc/ssh && \
    (ssh-keyscan -t rsa github.com >> /etc/ssh/ssh_known_hosts 2>/dev/null || true) && \
    git config --global core.autocrlf input && \
    git config --global core.pager 'cat' && \
    git config --global init.defaultBranch main && \
    git config --global safe.directory '*'

WORKDIR /workspace

# ────────────────────────────────────────────────────────────────────────────────
# STAGE 2: Python Runtime + Global Tools
# ────────────────────────────────────────────────────────────────────────────────
FROM base-system AS python-runtime

ENV PYTHON_VERSION=3.13 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Python 3.13 from deadsnakes PPA (with fallback to system python 3.12)
RUN apt-get update && \
    (add-apt-repository -y ppa:deadsnakes/ppa || echo "PPA failed, using system Python") && \
    apt-get update && \
    (apt-get install -y --no-install-recommends \
    python3.13 python3.13-dev python3.13-venv \
    python3-pip python3-dev \
    libpq-dev libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/* && apt-get clean) || \
    (echo "Python 3.13 not available, falling back to system python3..." && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 python3-dev python3-pip python3-venv \
    libpq-dev libssl-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/*)

# Set Python 3.13 as default + ensure pip works
RUN (update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 2 2>/dev/null || true) && \
    (update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 2>/dev/null || true) && \
    (update-alternatives --install /usr/bin/python python /usr/bin/python3.13 2 2>/dev/null || true) && \
    (update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1 2>/dev/null || true) && \
    update-alternatives --auto python3 2>/dev/null || true && \
    update-alternatives --auto python 2>/dev/null || true && \
    python3 -m ensurepip --upgrade 2>/dev/null || true && \
    python3 -m pip install --break-system-packages --upgrade pip 2>/dev/null || true

# Install UV (fast Python package manager)
RUN --mount=type=cache,target=/root/.cache/pip \
    curl -LsSf https://astral.sh/uv/install.sh | sh || \
    (pip3 install --break-system-packages uv && \
    ln -sf /usr/local/bin/uv /usr/local/bin/uv) && \
    (mv /root/.local/bin/uv /usr/local/bin/uv 2>/dev/null || \
    ln -sf /root/.local/bin/uv /usr/local/bin/uv) && \
    uv --version || echo "UV installation failed, will use pip"

# Install global Python tools via UV (one package per call — UV requirement)
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/uv \
    uv tool install --force black && \
    uv tool install --force ruff && \
    uv tool install --force pytest && \
    uv tool install --force mypy && \
    uv tool install --force pylint && \
    uv tool install --force pre-commit && \
    uv tool install --force httpie && \
    uv tool install --force rich-cli && \
    uv tool install --force typer-cli || \
    echo "Some UV tool installs failed - will install in post-create.sh"

ENV PATH="/root/.local/bin:$PATH"

# ────────────────────────────────────────────────────────────────────────────────
# STAGE 3: Node.js Runtime + Frontend Tools
# ────────────────────────────────────────────────────────────────────────────────
FROM python-runtime AS node-runtime

ENV NODE_VERSION=24 \
    NPM_CONFIG_PREFIX=/home/wfc/.npm-global

# Install Node.js 24 LTS from NodeSource
RUN (curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/* && apt-get clean) || \
    (echo "NodeSource 24 failed, trying 22..." && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/* && apt-get clean) || \
    (echo "NodeSource failed, trying system nodejs..." && \
    apt-get update && apt-get install -y nodejs npm && \
    rm -rf /var/lib/apt/lists/*)

ENV PATH="${NPM_CONFIG_PREFIX}/bin:${PATH}"

# Install pnpm + bun + global packages (one layer)
# Use npm for global installs — NPM_CONFIG_PREFIX=/home/wfc/.npm-global is in PATH
# and accessible by the wfc user (pnpm global requires PNPM_HOME which is fragile)
RUN --mount=type=cache,target=/root/.npm \
    npm install -g \
    pnpm@latest \
    typescript@latest \
    vite@latest \
    @vitejs/plugin-react@latest \
    eslint@latest \
    prettier@latest \
    tailwindcss@latest \
    @anthropic-ai/claude-code@latest \
    opencode-ai@latest && \
    pnpm config set store-dir /home/wfc/.pnpm-store && \
    (curl -fsSL https://bun.sh/install | bash || \
    echo "Bun installation failed, continuing...")

# ────────────────────────────────────────────────────────────────────────────────
# STAGE 4: System-Level CLIs (root required)
# Only tools that need apt repos or /usr/local/bin access.
# User-level tools (Oh My Zsh, Kiro, Entire, Bun) install as wfc user in Stage 5.
# ────────────────────────────────────────────────────────────────────────────────
FROM node-runtime AS dev-tools

ARG USERNAME=wfc

# Docker CLI + GitHub CLI + Starship (all need root for system paths)
RUN (curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list || true) && \
    (curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list || true) && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin gh && \
    rm -rf /var/lib/apt/lists/* || \
    echo "Docker/gh CLI installation failed"

# Starship prompt (installs to /usr/local/bin — needs root)
RUN sh -c "$(curl -fsSL https://starship.rs/install.sh)" "" --yes || \
    echo "Starship installation failed"

# ────────────────────────────────────────────────────────────────────────────────
# STAGE 5: Final Image — User config + WFC
# This is the most volatile stage. Changes here rebuild quickly because
# all heavy installs are cached in earlier stages.
# ────────────────────────────────────────────────────────────────────────────────
FROM dev-tools AS devcontainer

ARG USERNAME=wfc
ARG USER_GID=1000

# Directories + permissions + git config (one layer)
# chown entire home dir — dev-tools stage creates files as root (Oh My Zsh, Starship)
RUN mkdir -p \
    /workspace/app /workspace/repos /workspace/tmp /workspace/.devcontainer \
    /home/$USERNAME/.local/bin /home/$USERNAME/.local/share /home/$USERNAME/.cache/claude \
    /opt/wfc/home-defaults && \
    chown -R $USERNAME:$USERNAME /workspace && \
    chown -R $USERNAME:$USERNAME /home/$USERNAME && \
    chown -R $USERNAME:$USERNAME /opt/wfc/home-defaults && \
    chmod 755 /home/$USERNAME/.local && \
    chmod 755 /home/$USERNAME/.cache

# Switch to non-root user
USER $USERNAME

# Git config + SSH dir (one layer)
RUN mkdir -p ~/.ssh && chmod 700 ~/.ssh && \
    (git config --global user.name "WFC Dev" || true) && \
    (git config --global user.email "dev@wfc.local" || true) && \
    (git config --global credential.helper store || true) && \
    (git config --global init.defaultBranch main || true) && \
    (git config --global core.autocrlf input || true) && \
    (git config --global safe.directory '*' || true)

WORKDIR /workspace

ENV PATH="/home/wfc/.npm-global/bin:/home/wfc/.local/bin:/home/wfc/.bun/bin:$PATH" \
    FIREWALL_MODE=audit

# ── User-level tool installs (as wfc user — no root, no symlinks) ────────────
# Everything lands in ~/.local/bin, ~/.oh-my-zsh, ~/.bun — already in PATH

# Claude Code setup (shell integrations + config directory)
RUN mkdir -p ~/.claude && \
    (claude install --yes 2>/dev/null || \
    echo "claude install skipped (will configure on first interactive use)")

# Oh My Zsh + zshrc init (installs to ~/.oh-my-zsh)
RUN (sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended && \
    echo 'eval "$(starship init zsh)"' >> ~/.zshrc || \
    echo "Oh My Zsh failed")

# Kiro + Entire + Bun (all install to ~/.local/bin or ~/.bun)
RUN (curl -fsSL https://cli.kiro.dev/install | bash || \
    echo "Kiro CLI failed") && \
    (curl -fsSL https://entire.io/install.sh | bash || \
    echo "Entire CLI failed") && \
    (curl -fsSL https://bun.sh/install | bash || \
    echo "Bun failed")

# ── WFC Home Directory Defaults ──────────────────────────────────────────────
#
# Strategy: Write managed files to BOTH /home/wfc/ (Docker's first-run volume
# population) AND /opt/wfc/home-defaults/ (post-create sync on rebuilds).
#
# File categories:
#   MANAGED  (always overwritten from image) — .wfc_env, .wfc_motd.sh, .healthcheck.sh
#   SEEDED   (only created if missing)       — .bashrc, .zshrc, .ssh/config
#   USER     (never touched)                 — .claude/, .ssh/id_*, .config/gh/, .gitconfig
# ─────────────────────────────────────────────────────────────────────────────

# All managed files + seeded rc files + version marker (ONE layer)
RUN { \
    echo '# WFC environment — managed by devcontainer (do not edit, will be overwritten)'; \
    echo 'export PATH="/home/wfc/.npm-global/bin:/home/wfc/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"'; \
    echo 'export NODE_ENV=development'; \
    echo 'export NPM_CONFIG_PREFIX=/home/wfc/.npm-global'; \
    echo 'export PYTHONUNBUFFERED=1'; \
    echo 'export PYTHONDONTWRITEBYTECODE=1'; \
    echo ''; \
    echo '# WFC skill aliases — run skills directly from terminal'; \
    echo 'alias wfc-build="claude /wfc-build"'; \
    echo 'alias wfc-review="claude /wfc-review"'; \
    echo 'alias wfc-plan="claude /wfc-plan"'; \
    echo 'alias wfc-implement="claude /wfc-implement"'; \
    echo 'alias wfc-security="claude /wfc-security"'; \
    echo 'alias wfc-test="claude /wfc-test"'; \
    echo 'alias wfc-architecture="claude /wfc-architecture"'; \
    echo 'alias wfc-observe="claude /wfc-observe"'; \
    echo 'alias wfc-validate="claude /wfc-validate"'; \
    echo 'alias wfc-safeguard="claude /wfc-safeguard"'; \
    echo 'alias wfc-rules="claude /wfc-rules"'; \
    echo 'alias wfc-playground="claude /wfc-playground"'; \
    echo 'alias wfc-pr-comments="claude /wfc-pr-comments"'; \
    echo 'alias wfc-init="claude /wfc-init"'; \
    echo ''; \
    echo '# Convenience aliases'; \
    echo 'alias c="claude"'; \
    echo 'alias fw-audit="sudo tail -f /var/log/kern.log | grep FW-AUDIT"'; \
    echo 'alias fw-block="sudo tail -f /var/log/kern.log | grep FW-BLOCK"'; \
    } | tee /opt/wfc/home-defaults/.wfc_env > /home/$USERNAME/.wfc_env && \
    { \
    echo '#!/bin/bash'; \
    echo '# WFC MOTD banner — managed by devcontainer (do not edit, will be overwritten)'; \
    echo 'printf "\n"'; \
    echo 'printf "\e[38;5;197m██╗    ██╗\e[38;5;198m███████╗\e[38;5;199m ██████╗\e[0m\n"'; \
    echo 'printf "\e[38;5;197m██║    ██║\e[38;5;198m██╔════╝\e[38;5;199m██╔════╝\e[0m\n"'; \
    echo 'printf "\e[38;5;204m██║ █╗ ██║\e[38;5;205m█████╗  \e[38;5;206m██║     \e[0m\n"'; \
    echo 'printf "\e[38;5;211m██║███╗██║\e[38;5;212m██╔══╝  \e[38;5;213m██║     \e[0m\n"'; \
    echo 'printf "\e[38;5;218m╚███╔███╔╝\e[38;5;219m██║     \e[38;5;220m╚██████╗\e[0m\n"'; \
    echo 'printf "\e[38;5;225m ╚══╝╚══╝ \e[38;5;226m╚═╝     \e[38;5;227m ╚═════╝\e[0m\n"'; \
    echo 'printf "\n"'; \
    echo 'printf "\e[38;5;245m  World Fucking Class Development Environment\e[0m\n"'; \
    echo 'printf "\e[38;5;240m  ──────────────────────────────────────────\e[0m\n"'; \
    echo 'printf "\e[38;5;75m  Python\e[0m  $(python3 --version 2>/dev/null | cut -d\" \" -f2)"; printf "    "'; \
    echo 'printf "\e[38;5;70m  Node\e[0m  $(node --version 2>/dev/null)"; printf "    "'; \
    echo 'printf "\e[38;5;141m  Claude\e[0m  $(claude --version 2>/dev/null | head -1 || echo \"n/a\")\n"'; \
    echo 'printf "\e[38;5;208m  gh\e[0m  $(gh --version 2>/dev/null | head -1 | cut -d\" \" -f3 || echo \"n/a\")"; printf "          "'; \
    echo 'printf "\e[38;5;45m  entire\e[0m  $(entire version 2>/dev/null | head -1 || echo \"n/a\")"; printf "    "'; \
    echo 'printf "\e[38;5;203m  uv\e[0m  $(uv --version 2>/dev/null | cut -d\" \" -f2 || echo \"n/a\")\n"'; \
    echo 'printf "\e[38;5;240m  ──────────────────────────────────────────\e[0m\n"'; \
    echo 'printf "\e[38;5;245m  Workspace:\e[0m /workspace/app\n"'; \
    echo 'printf "\e[38;5;245m  Firewall:\e[0m  ${FIREWALL_MODE:-audit} mode\n"'; \
    echo 'printf "\e[38;5;245m  Skills:\e[0m    wfc-build · wfc-review · wfc-plan · wfc-security\n"'; \
    echo 'printf "\e[38;5;240m  ──────────────────────────────────────────\e[0m\n"'; \
    echo 'printf "\e[38;5;245m  Type \e[38;5;141mclaude\e[38;5;245m to start · \e[38;5;141mc\e[38;5;245m is aliased · \e[38;5;141mwfc-build\e[38;5;245m to ship\e[0m\n"'; \
    echo 'printf "\n"'; \
    } | tee /opt/wfc/home-defaults/.wfc_motd.sh > /home/$USERNAME/.wfc_motd.sh && \
    chmod +x /opt/wfc/home-defaults/.wfc_motd.sh && \
    chmod +x /home/$USERNAME/.wfc_motd.sh && \
    printf '#!/bin/sh\ncommand -v python3 >/dev/null 2>&1 && \ncommand -v node >/dev/null 2>&1 && \ncommand -v npm >/dev/null 2>&1 && \nexit 0\nexit 1\n' \
    | tee /opt/wfc/home-defaults/.healthcheck.sh > /home/$USERNAME/.healthcheck.sh && \
    chmod +x /opt/wfc/home-defaults/.healthcheck.sh && \
    chmod +x /home/$USERNAME/.healthcheck.sh && \
    touch /home/$USERNAME/.bashrc /home/$USERNAME/.zshrc && \
    echo 'source ~/.wfc_env' >> /home/$USERNAME/.bashrc && \
    echo 'source ~/.wfc_motd.sh' >> /home/$USERNAME/.bashrc && \
    echo 'source ~/.wfc_env' >> /home/$USERNAME/.zshrc && \
    echo 'source ~/.wfc_motd.sh' >> /home/$USERNAME/.zshrc && \
    echo "1.0.0" > /opt/wfc/home-defaults/.wfc_version

# Clone WFC framework + install skills (last — changes with every push to repo)
RUN git clone --depth 1 https://github.com/sam-fakhreddine/wfc.git /workspace/repos/wfc 2>/dev/null && \
    (cd /workspace/repos/wfc && bash install-universal.sh --ci 2>/dev/null || \
    echo "WFC skill install skipped") || \
    echo "WFC clone skipped (will be available when workspace is mounted)"

# Set zsh as default shell
RUN sudo chsh -s /bin/zsh $USERNAME 2>/dev/null || true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /home/wfc/.healthcheck.sh

CMD ["/bin/zsh"]
