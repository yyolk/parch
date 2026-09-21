FROM ghcr.io/astral-sh/uv:0.12.17 AS uv
FROM mcr.microsoft.com/devcontainers/python:3.14

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends poppler-utils time \
    && rm -rf /var/lib/apt/lists/* \
    && printf '%s\n' \
        '# Prefer GNU time over bash reserved-word time in interactive shells.' \
        "alias time='/usr/bin/time'" \
        > /etc/profile.d/gnu-time.sh \
    && printf '\n%s\n' \
        '# GNU time: interactive non-login bash (VS Code / Codespaces terminal).' \
        '[ -f /etc/profile.d/gnu-time.sh ] && . /etc/profile.d/gnu-time.sh' \
        >> /etc/bash.bashrc
COPY --from=uv /uv /uvx /usr/local/bin/

# Venv lives outside the workspace so a bind-mounted repo does not hide it.
ENV UV_PROJECT_ENVIRONMENT=/home/vscode/.venv \
    UV_LINK_MODE=copy \
    UV_PYTHON_PREFERENCE=only-system \
    PATH="/home/vscode/.venv/bin:${PATH}"

USER vscode
WORKDIR /tmp/parch
COPY --chown=vscode:vscode pyproject.toml uv.lock README.md LICENSE ./
COPY --chown=vscode:vscode src ./src
RUN uv sync --all-groups --frozen \
    && rm -rf /home/vscode/.cache/uv

WORKDIR /home/vscode
