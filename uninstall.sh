#!/bin/bash
set -euo pipefail

echo "Uninstalling refract..."

if command -v pipx >/dev/null 2>&1; then
    pipx uninstall refract 2>/dev/null || true
fi
python3 -m pip uninstall -y refract 2>/dev/null || true

if [ -e "${HOME}/.local/bin/refract" ] || [ -L "${HOME}/.local/bin/refract" ]; then
    rm -f "${HOME}/.local/bin/refract"
    echo "Removed ${HOME}/.local/bin/refract"
fi

echo "Uninstallation complete."
echo "Virtual environments in ~/.refract/envs/ were left in place."
echo "To remove them completely, run: rm -rf ~/.refract"
