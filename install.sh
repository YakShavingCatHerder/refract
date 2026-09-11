#!/bin/bash
set -euo pipefail

usage() {
    cat <<'EOF'
Install Refract from this source tree.

Usage:
  ./install.sh          Python 3 only (copy refract.py onto PATH)
  ./install.sh --pip    python3 + pip (editable install)
  ./install.sh --pipx   python3 + pipx (editable install)
  ./install.sh --help

After any method, this script runs: refract install
that sets up ~/.refract/ and shell integration. It does not
install the executable; these methods do that.

pipx is optional and only used when --pipx is passed.
EOF
}

ensure_local_bin_on_path() {
    local export_line='export PATH="$HOME/.local/bin:$PATH"'
    local rc
    case "$(basename "${SHELL:-}")" in
        zsh) rc="$HOME/.zshrc" ;;
        bash) rc="$HOME/.bashrc" ;;
        *) rc="$HOME/.profile" ;;
    esac

    mkdir -p "$HOME/.local/bin"
    export PATH="$HOME/.local/bin:$PATH"

    if [ -f "$rc" ] && grep -Fqs "$export_line" "$rc"; then
        return
    fi
    printf '\n# Added by refract\n%s\n' "$export_line" >> "$rc"
    echo "[refract] Added ~/.local/bin to PATH in $rc"
}

install_python_only() {
    echo "Installing refract with Python 3 only..."
    chmod +x "$ROOT/refract.py"
    cp "$ROOT/refract.py" "$HOME/.local/bin/refract"
    chmod +x "$HOME/.local/bin/refract"
    echo "[refract] Installed $HOME/.local/bin/refract"
}

install_with_pip() {
    echo "Installing refract with python3 + pip..."
    python3 -m pip install --user --editable "$ROOT"
}

install_with_pipx() {
    echo "Installing refract with python3 + pipx..."
    if ! command -v pipx >/dev/null 2>&1; then
        echo "pipx was not found. Install pipx, or use ./install.sh or ./install.sh --pip." >&2
        exit 1
    fi
    pipx install --editable "$ROOT"
}

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

case "${1:-}" in
    ""|--pip|--pipx) ;;
    -h|--help) usage; exit 0 ;;
    *)
        echo "Unknown option: $1" >&2
        usage >&2
        exit 1
        ;;
esac

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required." >&2
    exit 1
fi

ensure_local_bin_on_path

case "${1:-}" in
    --pip) install_with_pip ;;
    --pipx) install_with_pipx ;;
    *) install_python_only ;;
esac

echo "Initializing Refract config and shell integration..."
refract install

echo
echo "Source install complete."
echo "Restart your shell, or run: source ~/.zshrc"
echo "  (bash users: source ~/.bashrc)"
echo "Then try: refract list"
