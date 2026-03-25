FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    sudo \
    curl \
    wget \
    ca-certificates \
    gnupg \
    lsb-release \
    procps \
    util-linux \
    kmod \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

RUN apt-get update && apt-get install -y python3-pytest python3-pytest-cov && \
    rm -rf /var/lib/apt/lists/*

# Add uv to PATH
ENV PATH="/root/.local/bin:${PATH}"

# Create both users to support devcontainer development and isolated test scenarios
RUN useradd -m -s /bin/bash tester && \
    useradd -m -s /bin/bash vscode && \
    echo "tester ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# By default, run pytest for testing
CMD ["pytest", "-v", "--cov=app", "--cov-report=term-missing", "--tb=short"]
