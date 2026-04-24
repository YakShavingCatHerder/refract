#!/bin/bash

# Install refract using pip
echo "Installing refract..."
if pip3 help install 2>/dev/null | rg -q -- "--break-system-packages"; then
    pip3 install -e . --user --break-system-packages
else
    pip3 install -e . --user
fi

# Make sure the script is executable
echo "Setting up permissions..."
chmod +x refract.py

# Run the install command to set up symlink and PATH
echo "Setting up refract globally..."
python3 -m refract install

echo "Installation complete! You can now use 'refract' from anywhere."
echo "Try: refract --help"
