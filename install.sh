#!/bin/bash
set -euo pipefail

usage() {
    cat <<'EOF'
Install Refract from this source tree.

Usage:
  ./install.sh          Python 3 only (copy refract.py onto PATH)
  ./install.sh --pip    python3 + pip (editable install)
  ./install.sh --help

After either method, this script runs: refract install
that sets up ~/.refract/ and shell integration. It does not
install the executable; these two methods do that.

pipx is not required.
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

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

case "${1:-}" in
    "" ) ;;
    --pip) ;;
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

if [ "${1:-}" = "--pip" ]; then
    install_with_pip
else
    install_python_only
fi

echo "Initializing Refract config and shell integration..."
refract install

echo
echo "Source install complete."
echo "Restart your shell, or run: source ~/.zshrc"
echo "  (bash users: source ~/.bashrc)"
echo "Then try: refract list"
