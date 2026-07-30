#!/usr/bin/env python3

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
PROMPT_SNIPPET_START = "# >>> refract prompt integration >>>"
PROMPT_SNIPPET_END = "# <<< refract prompt integration <<<"

# Standard 8 ANSI color names supported by zsh and bash
COLOR_NAMES = frozenset({
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
})

# Bash SGR codes: (foreground, background)
BASH_COLOR_CODES = {
    "black": (30, 40),
    "red": (31, 41),
    "green": (32, 42),
    "yellow": (33, 43),
    "blue": (34, 44),
    "magenta": (35, 45),
    "cyan": (36, 46),
    "white": (37, 47),
}

DEFAULT_COLORWAY = {"background": None, "text": "white"}


def load_config():
    ensure_dirs()
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(config):
    ensure_dirs()
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def get_colorway():
    config = load_config()
    colorway = config.get("colorway", DEFAULT_COLORWAY)
    return colorway.get("background"), colorway.get("text", "white")


def validate_color(name):
    return name.lower() in COLOR_NAMES


def build_prompt_snippets(background, text):
    """Build zsh and bash prompt snippets for the given colorway."""
    zsh_style = f"%K{{{background}}}%F{{{text}}}" if background else f"%F{{{text}}}"
    zsh_reset = "%f%k" if background else "%f"
    zsh_snippet = f"""{PROMPT_SNIPPET_START}
setopt PROMPT_SUBST 2>/dev/null || true
autoload -Uz add-zsh-hook 2>/dev/null || true
_refract_precmd() {{
  [ -z "$REFRACT_ENV" ] && return
  local refract_prefix="%{{{zsh_style}}}[refract:$REFRACT_ENV]%{{{zsh_reset}}} "
  case "$PROMPT" in
    "$refract_prefix"*) ;;
    *) PROMPT="$refract_prefix$PROMPT" ;;
  esac
}}
add-zsh-hook precmd _refract_precmd 2>/dev/null || true
{PROMPT_SNIPPET_END}"""

    fg_code, bg_code = BASH_COLOR_CODES[text][0], BASH_COLOR_CODES[background][1]
    bash_open = f"\\[\\e[{bg_code};{fg_code}m\\]"
    bash_close = "\\[\\e[0m\\]"
    bash_snippet = f"""{PROMPT_SNIPPET_START}
__refract_prompt_command() {{
  [ -z "$REFRACT_ENV" ] && return
  local refract_prefix="{bash_open}[refract:$REFRACT_ENV]{bash_close} "
  case "$PS1" in
    "$refract_prefix"*) ;;
    *) PS1="$refract_prefix$PS1" ;;
  esac
}}
case ";$PROMPT_COMMAND;" in
  *";__refract_prompt_command;"*) ;;
  *) PROMPT_COMMAND="${{PROMPT_COMMAND:+$PROMPT_COMMAND; }}__refract_prompt_command" ;;
esac
{PROMPT_SNIPPET_END}"""

    return zsh_snippet, bash_snippet


def build_default_prompt_snippets():
    """Build prompt snippets using the default colorway (white text, no background)."""
    zsh_snippet = f"""{PROMPT_SNIPPET_START}
setopt PROMPT_SUBST 2>/dev/null || true
autoload -Uz add-zsh-hook 2>/dev/null || true
_refract_precmd() {{
  [ -z "$REFRACT_ENV" ] && return
  local refract_prefix="%{{%F{{white}}%}}[refract:$REFRACT_ENV]%{{%f%}} "
  case "$PROMPT" in
    "$refract_prefix"*) ;;
    *) PROMPT="$refract_prefix$PROMPT" ;;
  esac
}}
add-zsh-hook precmd _refract_precmd 2>/dev/null || true
{PROMPT_SNIPPET_END}"""

    bash_snippet = f"""{PROMPT_SNIPPET_START}
__refract_prompt_command() {{
  [ -z "$REFRACT_ENV" ] && return
  local refract_prefix="\\[\\e[1;37m\\][refract:$REFRACT_ENV]\\[\\e[0m\\] "
  case "$PS1" in
    "$refract_prefix"*) ;;
    *) PS1="$refract_prefix$PS1" ;;
  esac
}}
case ";$PROMPT_COMMAND;" in
  *";__refract_prompt_command;"*) ;;
  *) PROMPT_COMMAND="${{PROMPT_COMMAND:+$PROMPT_COMMAND; }}__refract_prompt_command" ;;
esac
{PROMPT_SNIPPET_END}"""

    return zsh_snippet, bash_snippet


def ensure_symlink():
    """Create a symlink for manual installation (not needed when installed via pip)"""
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


def _write_prompt_snippet(config_path, snippet, force_update=False):
    """Write or update prompt integration snippet in a shell config file."""
    if config_path.exists():
        existing = config_path.read_text()
        if PROMPT_SNIPPET_START in existing:
            if not force_update:
                return False
            start = existing.index(PROMPT_SNIPPET_START)
            end = existing.index(PROMPT_SNIPPET_END) + len(PROMPT_SNIPPET_END)
            config_path.write_text(existing[:start] + snippet + existing[end:])
            return True
    with open(config_path, "a") as f:
        f.write("\n" + snippet + "\n")
    return True


def ensure_prompt_integration(force_update=False):
    """Install shell prompt hooks that render [refract:<env>] from REFRACT_ENV."""
    background, text = get_colorway()
    if background:
        zsh_snippet, bash_snippet = build_prompt_snippets(background, text)
    else:
        zsh_snippet, bash_snippet = build_default_prompt_snippets()

    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        target = Path.home() / ".zshrc"
        changed = _write_prompt_snippet(target, zsh_snippet, force_update)
        if changed:
            action = "Updated" if force_update else "Added"
            print(f"[refract] {action} prompt integration in ~/.zshrc")
    elif "bash" in shell:
        target = Path.home() / ".bashrc"
        changed = _write_prompt_snippet(target, bash_snippet, force_update)
        if changed:
            action = "Updated" if force_update else "Added"
            print(f"[refract] {action} prompt integration in {target}")


def set_colorway(spec):
    """Set prompt colors as background/text (e.g. green/black)."""
    parts = spec.split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        print("Usage: refract colorway <background>/<text>")
        print("Example: refract colorway green/black")
        return

    background, text = parts[0].strip().lower(), parts[1].strip().lower()
    invalid = [c for c in (background, text) if not validate_color(c)]
    if invalid:
        supported = ", ".join(sorted(COLOR_NAMES))
        print(f"Invalid color(s): {', '.join(invalid)}")
        print(f"Supported colors: {supported}")
        return

    config = load_config()
    config["colorway"] = {"background": background, "text": text}
    save_config(config)

    updated = []
    background, text = get_colorway()
    zsh_snippet, bash_snippet = build_prompt_snippets(background, text)
    for path, snippet in [(Path.home() / ".zshrc", zsh_snippet),
                          (Path.home() / ".bashrc", bash_snippet)]:
        if _write_prompt_snippet(path, snippet, force_update=True):
            updated.append(str(path))

    print(f"[refract] Colorway set to {background} background with {text} text.")
    if updated:
        print(f"[refract] Updated prompt integration in: {', '.join(updated)}")
    print("[refract] Restart your shell or run 'source ~/.zshrc' to apply.")


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

# Set stable env marker for prompt integrations
export REFRACT_ENV="{name}"

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

def show_current_env():
    """Show the currently active refract environment"""
    refract_env = os.environ.get("REFRACT_ENV")
    if refract_env:
        background, text = get_colorway()
        if background:
            fg, bg = BASH_COLOR_CODES[text][0], BASH_COLOR_CODES[background][1]
            color = f"\033[{bg};{fg}m"
        else:
            color = "\033[1;37m"
        print(f"Currently in refract environment: {color}{refract_env}\033[0m")
        return refract_env
    else:
        print("No refract environment currently active")
        return None


def print_usage():
    print("""
refract - Lightweight Virtualenv Manager

Usage:
  refract install           Install refract globally (create symlink and update PATH)
  refract init <env_name>   Create a new virtual environment
  refract list              List all existing virtual environments
  refract use <env_name>    Activate the specified environment
  refract current           Show currently active environment
  refract rm <env_name>     Delete the specified virtual environment
  refract colorway <bg>/<fg>  Set prompt colors (e.g. green/black)

Examples:
  refract install
  refract init myenv
  refract list
  refract use myenv
  refract current
  refract rm myenv
  refract colorway green/black
    """)


def main():
    """Main entry point for the refract command-line tool"""
    args = sys.argv[1:]
    debug_mode = '--debug' in args
    if debug_mode:
        print(f"[DEBUG] refract_HOME is set to: {REFRACT_HOME}")
    args = [arg for arg in args if arg != '--debug']    
    # Handle special commands first
    if args and args[0] == "install":
        ensure_symlink()
        ensure_local_bin_in_path()
        ensure_prompt_integration()
        return
    
    ensure_dirs()
    ensure_prompt_integration()

    if not args:
        print_usage()
        return

    cmd = args[0]
    if cmd == "list":
        list_envs()
    elif cmd == "init" and len(args) >= 2:
        create_env(args[1])
    elif cmd == "use" and len(args) >= 2:
        activate_env(args[1])
    elif cmd == "current":
        show_current_env()
    elif cmd == "rm" and len(args) >= 2:
        remove_env(args[1])
    elif cmd == "colorway" and len(args) >= 2:
        set_colorway(args[1])
    else:
        print("Invalid command or missing arguments.\n")
        print_usage()


if __name__ == "__main__":
    main()
