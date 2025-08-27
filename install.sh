#!/bin/bash

# Install refract using pip
echo "Installing refract..."
pip3 install -e . --user --break-system-packages

# Make sure the script is executable
echo "Setting up permissions..."
chmod +x refract.py

# Run the install command to set up symlink and PATH
echo "Setting up refract globally..."
python3 -m refract install

echo "Installation complete! You can now use 'refract' from anywhere."
echo "Try: refract --help"
