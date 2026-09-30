FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Install all system tools in a single layer (rarely changes - good for cache)
# hadolint ignore=DL3008
RUN apt-get update \
    # Install base dependencies for adding repositories
    && apt-get install -y --no-install-recommends \
        curl \
        wget \
        ca-certificates \
        gnupg \
        lsb-release \
        cmake \
        libpam0g-dev \
    # Add GitHub CLI repository
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list \
    # Add Node.js repository
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    # Add HashiCorp repository
    && curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /etc/apt/keyrings/hashicorp-archive-keyring.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list \
    # Add 1Password repository
    && curl -fsSL https://downloads.1password.com/linux/keys/1password.asc | gpg --dearmor -o /etc/apt/keyrings/1password-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" | tee /etc/apt/sources.list.d/1password.list \
    # Update with new repositories and install ALL packages in one command
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        g++ \
        zlib1g-dev \
        git \
        jq \
        yq \
        zsh \
        unzip \
        nodejs \
        gh \
        terraform \
        vault \
        consul \
        nomad \
        1password-cli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2 and golangci-lint (rarely changes - good for cache)
# Both are picked for the platform being built: the arm64 image used to get
# the x86_64 AWS CLI. golangci-lint is a pinned release checked against its
# own sha256: install.sh from master now also matches the .sbom.json line of
# the checksums file and rejects a sound archive. To move it, take both sums
# from golangci-lint-<version>-checksums.txt (the .tar.gz lines only).
ARG TARGETARCH
ARG GOLANGCI_LINT_VERSION=2.14.0
ARG GOLANGCI_LINT_SHA256_AMD64=ab90aeb7b066f92a33415b638a50fe5344bbb75a0d32ad30cc248d88f81032ab
ARG GOLANGCI_LINT_SHA256_ARM64=ee7ec5f3453d15ddf106fae5a4d6c71737712348a979d1fe9cd52ec7ea299bae
RUN set -eu; \
    case "${TARGETARCH}" in \
        amd64) aws_arch=x86_64; gl_sum="${GOLANGCI_LINT_SHA256_AMD64}" ;; \
        arm64) aws_arch=aarch64; gl_sum="${GOLANGCI_LINT_SHA256_ARM64}" ;; \
        *) echo "unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    gl="golangci-lint-${GOLANGCI_LINT_VERSION}-linux-${TARGETARCH}"; \
    curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${aws_arch}.zip" -o /tmp/awscliv2.zip & \
    curl -fsSL "https://github.com/golangci/golangci-lint/releases/download/v${GOLANGCI_LINT_VERSION}/${gl}.tar.gz" -o /tmp/golangci-lint.tar.gz & \
    wait; \
    echo "${gl_sum}  /tmp/golangci-lint.tar.gz" | sha256sum -c -; \
    tar -xzf /tmp/golangci-lint.tar.gz -C /tmp; \
    install -m 0755 "/tmp/${gl}/golangci-lint" /usr/local/bin/golangci-lint; \
    unzip -q /tmp/awscliv2.zip -d /tmp; \
    /tmp/aws/install; \
    rm -rf /tmp/awscliv2.zip /tmp/aws /tmp/golangci-lint.tar.gz "/tmp/${gl}"

# Switch to vscode user
USER vscode
WORKDIR /home/vscode

# Create directories for persistent volumes
RUN mkdir -p /home/vscode/.cache \
    /home/vscode/.config \
    /home/vscode/.config/op \
    /home/vscode/.zsh_history_dir \
    /home/vscode/.local/bin \
    /home/vscode/.claude \
    /home/vscode/.local/share/@anthropic \
    # Set strict permissions for 1Password config directory
    && chmod 700 /home/vscode/.config/op

# Install Oh My Zsh and themes in parallel (rarely changes - good for cache)
RUN rm -rf "$HOME/.oh-my-zsh" && \
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended && \
    git clone --depth=1 https://github.com/romkatv/powerlevel10k.git \
        "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k" & \
    git clone --depth=1 https://github.com/dracula/zsh.git \
        "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/dracula" & \
    wait

# Copy p10k configuration (changes rarely)
COPY --chown=vscode:vscode p10k.sh /home/vscode/.p10k.zsh

# Configure npm for local global packages (no sudo needed)
RUN mkdir -p /home/vscode/.local/share/npm-global && \
    npm config set prefix '/home/vscode/.local/share/npm-global'

# Configure zshrc (changes rarely)
RUN sed -i 's/^ZSH_THEME=.*/ZSH_THEME="powerlevel10k\/powerlevel10k"/' "$HOME/.zshrc" && \
    { \
        echo ''; \
        echo '# To customize prompt, run "p10k configure" or edit ~/.p10k.zsh'; \
        echo '[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh'; \
        echo ''; \
        echo '# Persistent zsh history'; \
        echo 'export HISTFILE=~/.zsh_history_dir/.zsh_history'; \
        echo 'export HISTSIZE=10000'; \
        echo 'export SAVEHIST=10000'; \
        echo ''; \
        echo '# npm global packages path'; \
        echo 'export PATH="/home/vscode/.local/share/npm-global/bin:$PATH"'; \
        echo ''; \
        echo '# Super Claude alias'; \
        echo 'alias super-claude="claude --dangerously-skip-permissions --mcp-config /home/vscode/.devcontainer/mcp.json"'; \
    } >> "$HOME/.zshrc"

# Install npm global packages as vscode user (no root needed)
RUN npm install -g @anthropic-ai/claude-code@latest @bazel/bazelisk

# Set working directory
WORKDIR /workspace
