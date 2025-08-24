#!/bin/bash

echo "Uninstalling refract..."

# Remove the symlink
if [ -L ~/.local/bin/refract ]; then
    rm ~/.local/bin/refract
    echo "Removed symlink from ~/.local/bin/refract"
fi

# Uninstall the package
pip3 uninstall refract -y

# Remove the refract home directory (optional - uncomment if you want to remove all environments)
# rm -rf ~/.refract

echo "Uninstallation complete!"
echo "Note: Your virtual environments in ~/.refract/envs/ are still available."
echo "To remove them completely, run: rm -rf ~/.refract"
