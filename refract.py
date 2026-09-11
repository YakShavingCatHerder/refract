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
WRAPPER_SNIPPET_START = "# >>> refract shell wrapper >>>"
WRAPPER_SNIPPET_END = "# <<< refract shell wrapper <<<"

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

DEFAULT_COLORWAY = {"background": "green", "text": "black"}


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
    return colorway.get("background", DEFAULT_COLORWAY["background"]), colorway.get("text", DEFAULT_COLORWAY["text"])


def validate_color(name):
    return name.lower() in COLOR_NAMES


def build_prompt_snippets(background, text):
    """Build zsh and bash prompt snippets for the given colorway."""
    if background:
        zsh_prefix_open = f"%{{%K{{{background}}}%F{{{text}}}%}}"
        zsh_prefix_close = "%{%f%k%}"
    else:
        zsh_prefix_open = f"%{{%F{{{text}}}%}}"
        zsh_prefix_close = "%{%f%}"
    zsh_snippet = f"""{PROMPT_SNIPPET_START}
setopt PROMPT_SUBST 2>/dev/null || true
autoload -Uz add-zsh-hook 2>/dev/null || true
_refract_precmd() {{
  [ -z "$REFRACT_ENV" ] && return
  local refract_prefix="{zsh_prefix_open}[refract:$REFRACT_ENV]{zsh_prefix_close} "
  case "$PROMPT" in
    "$refract_prefix"*) ;;
    *) PROMPT="$refract_prefix$PROMPT" ;;
  esac
}}
add-zsh-hook precmd _refract_precmd 2>/dev/null || true
{PROMPT_SNIPPET_END}"""

    fg_code = BASH_COLOR_CODES[text][0]
    if background:
        bg_code = BASH_COLOR_CODES[background][1]
        bash_open = f"\\[\\e[{bg_code};{fg_code}m\\]"
    else:
        bash_open = f"\\[\\e[1;{fg_code}m\\]"
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


ZSH_SHELL_WRAPPER = f"""{WRAPPER_SNIPPET_START}
refract() {{
  if [[ "$1" == "colorway" && -n "$2" ]]; then
    REFRACT_COLORWAY_RELOAD=1 command refract "$@"
  else
    command refract "$@"
  fi
  local ret=$?
  if (( ret == 0 )) && [[ "$1" == "colorway" && -n "$2" ]]; then
    if [[ -n "$REFRACT_ENV" && "$PROMPT" == *"[refract:$REFRACT_ENV]"* ]]; then
      PROMPT="${{PROMPT#*[refract:$REFRACT_ENV] }}"
    fi
    source "${{ZDOTDIR:-$HOME}}/.zshrc" 2>/dev/null || true
    (( ${{+functions[_refract_precmd]}} )) && _refract_precmd
  fi
  return ret
}}
{WRAPPER_SNIPPET_END}"""

BASH_SHELL_WRAPPER = f"""{WRAPPER_SNIPPET_START}
refract() {{
  if [[ "$1" == "colorway" && -n "$2" ]]; then
    REFRACT_COLORWAY_RELOAD=1 command refract "$@"
  else
    command refract "$@"
  fi
  local ret=$?
  if [[ $ret -eq 0 && "$1" == "colorway" && -n "$2" ]]; then
    if [[ -n "$REFRACT_ENV" && "$PS1" == *"[refract:$REFRACT_ENV]"* ]]; then
      PS1="${{PS1#*[refract:$REFRACT_ENV] }}"
    fi
    source "$HOME/.bashrc" 2>/dev/null || true
    type __refract_prompt_command &>/dev/null && __refract_prompt_command
  fi
  return $ret
}}
{WRAPPER_SNIPPET_END}"""


def ensure_dirs():
    ENVS_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'w') as f:
            json.dump({"active": None, "colorway": DEFAULT_COLORWAY}, f)


def _write_marked_snippet(config_path, snippet, start_marker, end_marker, force_update=False):
    """Write or update a marked snippet in a shell config file."""
    if config_path.exists():
        existing = config_path.read_text()
        if start_marker in existing:
            if not force_update:
                return False
            start = existing.index(start_marker)
            end = existing.index(end_marker) + len(end_marker)
            config_path.write_text(existing[:start] + snippet + existing[end:])
            return True
    with open(config_path, "a") as f:
        f.write("\n" + snippet + "\n")
    return True


def _write_prompt_snippet(config_path, snippet, force_update=False):
    return _write_marked_snippet(
        config_path, snippet, PROMPT_SNIPPET_START, PROMPT_SNIPPET_END, force_update
    )


def _write_shell_wrapper(config_path, snippet, force_update=False):
    return _write_marked_snippet(
        config_path, snippet, WRAPPER_SNIPPET_START, WRAPPER_SNIPPET_END, force_update
    )


def setup_shell_integration(force_update=False):
    """Install prompt hooks and shell wrapper in zsh and bash configs."""
    ensure_dirs()
    background, text = get_colorway()
    zsh_prompt, bash_prompt = build_prompt_snippets(background, text)

    prompt_updated = []
    wrapper_updated = []
    shell_configs = (
        (Path.home() / ".zshrc", zsh_prompt, ZSH_SHELL_WRAPPER),
        (Path.home() / ".bashrc", bash_prompt, BASH_SHELL_WRAPPER),
    )
    for path, prompt_snippet, wrapper_snippet in shell_configs:
        if _write_prompt_snippet(path, prompt_snippet, force_update):
            prompt_updated.append(str(path))
        if _write_shell_wrapper(path, wrapper_snippet, force_update):
            wrapper_updated.append(str(path))

    return prompt_updated, wrapper_updated


def ensure_prompt_integration(force_update=False):
    """Install shell prompt hooks that render [refract:<env>] from REFRACT_ENV."""
    prompt_updated, _ = setup_shell_integration(force_update)
    for path in prompt_updated:
        action = "Updated" if force_update else "Added"
        print(f"[refract] {action} prompt integration in {path}")


def run_install():
    """Initialize Refract config and shell integration. Does not install the executable."""
    ensure_dirs()
    prompt_updated, wrapper_updated = setup_shell_integration(force_update=True)

    background, text = get_colorway()
    print(f"[refract] Initialized {REFRACT_HOME}")
    print(f"[refract] Default colorway: {background}/{text}")

    if prompt_updated:
        print(f"[refract] Installed prompt integration in: {', '.join(prompt_updated)}")
    if wrapper_updated:
        print(f"[refract] Installed shell wrapper in: {', '.join(wrapper_updated)}")

    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        rc_file = "~/.zshrc"
    elif "bash" in shell:
        rc_file = "~/.bashrc"
    else:
        rc_file = "~/.zshrc or ~/.bashrc"

    print("[refract] Shell integration is ready.")
    print(f"[refract] Restart your shell or run 'source {rc_file}' to activate.")


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
  refract install           Initialize config and shell integration
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
        run_install()
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
