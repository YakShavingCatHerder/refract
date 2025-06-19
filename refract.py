import os
import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Base directory for refract environments
REFRACT_HOME = Path.home() / ".refract"
ENVS_DIR = REFRACT_HOME / "envs"
CONFIG_PATH = REFRACT_HOME / "refract.json"

def ensure_symlink():
    # Path where the symlink should go
    bin_dir = os.path.expanduser("~/.local/bin")
    symlink_path = os.path.join(bin_dir, "refract")

    # Absolute path to this script
    actual_path = os.path.abspath(sys.argv[0])

    # Make sure bin_dir exists
    os.makedirs(bin_dir, exist_ok=True)

    # Only create symlink if it doesn't exist or is broken
    if not os.path.islink(symlink_path) or not os.path.exists(symlink_path):
        try:
            # Remove if it's a broken symlink or regular file
            if os.path.exists(symlink_path) or os.path.islink(symlink_path):
                os.remove(symlink_path)

            os.symlink(actual_path, symlink_path)
            print(f"[refract] Symlink created: {symlink_path} → {actual_path}")
        except PermissionError:
            print(f"[refract] ⚠️  Permission denied creating symlink at {symlink_path}.")
        except Exception as e:
            print(f"[refract] ⚠️  Could not create symlink: {e}")

    # Check if ~/.local/bin is in PATH 
    if bin_dir not in os.environ.get("PATH", ""):
        print(f"[refract] ⚠️  ~/.local/bin is not in your PATH. Add it to run 'refract' globally.")
        

def ensure_dirs():
    ENVS_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'w') as f:
            json.dump({"active": None}, f)


def list_envs():
    envs = [d.name for d in ENVS_DIR.iterdir() if d.is_dir()]
    if envs:
        print("Available virtualenvs:")
        for env in envs:
            print("  *", env)
    else:
        print("No environments found. Use 'refract init <name>' to create one.")


def create_env(name):
    env_path = ENVS_DIR / name
    if env_path.exists():
        print(f"Environment '{name}' already exists.")
        return
    if not name.isidentifier():
        print("Environment name must be a valid identifier (no spaces or special characters).")
        return 
    subprocess.run([sys.executable, "-m", "venv", str(env_path)])
    print(f"Created new virtualenv at {env_path}")
    ensure_local_bin_in_path()

def activate_env(name):
    env_path = ENVS_DIR / name
    activate_script = env_path / "bin" / "activate"

    if not activate_script.exists():
        print(f"Environment '{name}' does not exist.")
        return

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as tmp:
        script_path = tmp.name
        tmp.write(f"""#!/usr/bin/env bash
# Load user profile to get PATH, aliases, etc.
source ~/.profile 2>/dev/null || true
source ~/.bash_profile 2>/dev/null || true
source ~/.zshrc 2>/dev/null || true

# Source the venv
source "{activate_script}"

# Drop into your preferred shell
exec $SHELL --login
""")
    os.chmod(script_path, 0o755)

    print(f"[refract] Switching to environment '{name}'...")
    subprocess.run(["bash", script_path])

    # Optional: Cleanup temp file after use
    try:
        os.remove(script_path)
    except Exception:
        pass

def ensure_local_bin_in_path():
    bin_path = "$HOME/.local/bin"
    export_line = f'export PATH="{bin_path}:$PATH"\n'

    shell = os.environ.get("SHELL", "")
    config_files = []

    if "zsh" in shell:
        config_files = [Path.home() / ".zshrc"]
    elif "bash" in shell:
        config_files = [Path.home() / ".bash_profile", Path.home() / ".bashrc"]
    else:
        config_files = [Path.home() / ".profile"]

    for config in config_files:
        if config.exists():
            with open(config, "r") as f:
                if export_line.strip() in f.read():
                    return  # Already set

        # Append the export line
        with open(config, "a") as f:
            f.write(f"\n# Added by refract\n{export_line}")
        print(f"[refract] Added '{bin_path}' to PATH in {config}")
        return  # Only add to one file

def remove_env(name):
    env_path = ENVS_DIR / name
    if not env_path.exists():
        print(f"Environment '{name}' not found.")
        return
    subprocess.run(["rm", "-rf", str(env_path)])
    print(f"Removed environment '{name}'")


def print_usage():
    print("""
refract - Lightweight Virtualenv Manager

Usage:
  refract init <env_name>   Create a new virtual environment
  refract list              List all existing virtual environments
  refract use <env_name>    Show how to activate the specified environment
  refract rm <env_name>     Delete the specified virtual environment

Examples:
  refract init myenv
  refract list
  refract use myenv
  refract rm myenv
    """)


def main():
    args = sys.argv[1:]
    debug_mode = '--debug' in args
    if debug_mode:
        print(f"[DEBUG] refract_HOME is set to: {REFRACT_HOME}")
    args = [arg for arg in args if arg != '--debug']
    ensure_dirs()
    if len(sys.argv) < 2:
        print_usage()
        return

    if not args:
        print_usage()
        return

    cmd = args[0]
    if cmd == "list":
        list_envs()
    elif cmd == "init" and len(sys.argv) == 3:
        create_env(args[1])
    elif cmd == "use" and len(sys.argv) == 3:
        activate_env(sys.argv[2])
    elif cmd == "rm" and len(sys.argv) == 3:
        remove_env(sys.argv[2])
    else:
        print("Invalid command or missing arguments.\n")
        print_usage()


if __name__ == "__main__":
    main()
