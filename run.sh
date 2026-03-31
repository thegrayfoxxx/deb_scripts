#!/bin/bash

set -euo pipefail

PYTHON_SCRIPT="./main.py"
PYTHON_CMD="./.venv/bin/python3"
UV_BIN="${UV_BIN:-}"
UV_INSTALL_SCRIPT_URL="https://astral.sh/uv/install.sh"
EFFECTIVE_HOME="$(getent passwd "$(id -u)" | cut -d: -f6)"

if [[ -n "${EFFECTIVE_HOME}" ]]; then
    export HOME="${EFFECTIVE_HOME}"
fi

UV_ENV_FILE="${HOME}/.local/bin/env"
UV_DEFAULT_BIN="${HOME}/.local/bin/uv"
GLOBAL_BIN_DIR="/usr/local/bin"

ensure_global_uv_symlinks() {
    local source target current_target

    for binary in uv uvx uvw; do
        source="${HOME}/.local/bin/${binary}"
        target="${GLOBAL_BIN_DIR}/${binary}"

        [[ -e "${source}" ]] || continue

        if [[ -L "${target}" ]]; then
            current_target="$(readlink "${target}")"
            if [[ "${current_target}" == "${source}" ]]; then
                continue
            fi

            echo "❌ Симлинк ${target} уже указывает на другой файл / Symlink ${target} already points elsewhere" >&2
            return 1
        fi

        if [[ -e "${target}" ]]; then
            echo "❌ Файл ${target} уже существует и не является симлинком / File ${target} already exists and is not a symlink" >&2
            return 1
        fi

        ln -s "${source}" "${target}"
    done
}

if [[ -f "${UV_ENV_FILE}" ]]; then
    # shellcheck disable=SC1090
    source "${UV_ENV_FILE}"
fi

echo "🛠️ Подготовка окружения запуска / Preparing runtime environment..."

if [[ -z "$UV_BIN" ]]; then
    if command -v uv >/dev/null 2>&1; then
        UV_BIN="$(command -v uv)"
    elif [[ -x "${UV_DEFAULT_BIN}" ]]; then
        UV_BIN="${UV_DEFAULT_BIN}"
    fi
fi

if [[ -z "$UV_BIN" ]]; then
    echo "📦 UV не найден, выполняется установка / UV not found, installing..."

    if ! command -v curl >/dev/null 2>&1; then
        echo "📥 curl не найден, выполняется установка / curl not found, installing..."
        apt install -y curl
    fi

    curl -LsSf "${UV_INSTALL_SCRIPT_URL}" | sh

    if [[ -f "${UV_ENV_FILE}" ]]; then
        # shellcheck disable=SC1090
        source "${UV_ENV_FILE}"
    fi

    if command -v uv >/dev/null 2>&1; then
        UV_BIN="$(command -v uv)"
    elif [[ -x "${UV_DEFAULT_BIN}" ]]; then
        UV_BIN="${UV_DEFAULT_BIN}"
    else
        echo "❌ Установка UV завершена, но бинарный файл не найден / UV installation completed but the binary was not found" >&2
        exit 1
    fi

    echo "✅ UV установлен, продолжаем запуск / UV installed, continuing startup..."
else
    echo "✅ UV найден: ${UV_BIN} / UV found: ${UV_BIN}"
fi

if ! ensure_global_uv_symlinks; then
    exit 1
fi

if [[ -n "${UV_BIN}" ]]; then
    echo "🔄 Синхронизация окружения проекта / Syncing project environment..."
    "${UV_BIN}" sync
fi

echo "🚀 Подготовка окружения завершена / Environment preparation complete."

"${PYTHON_CMD}" "${PYTHON_SCRIPT}" "$@"
