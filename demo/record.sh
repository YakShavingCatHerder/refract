#!/bin/bash
# Record demo/refract.gif from demo/refract.tape.
# HOME lives under /tmp (macOS cannot create /var/folders/demo), but
# every on-screen path is rewritten to /var/folders/demo/home/...
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST_HOME="$HOME"
DEMO_ROOT="/tmp/test/demo"
DEMO_HOME="$DEMO_ROOT/home"
DEMO_BIN="$DEMO_ROOT/bin"
DISPLAY_HOME="/var/folders/demo/home"

cleanup() { rm -rf "$DEMO_ROOT"; }
trap cleanup EXIT

rm -rf "$DEMO_ROOT"
mkdir -p "$DEMO_BIN" "$DEMO_HOME/.cache"
cp "$ROOT/refract.py" "$DEMO_BIN/refract.py"
chmod +x "$DEMO_BIN/refract.py"

cat > "$DEMO_BIN/refract" <<EOF
#!/bin/bash
# use starts a nested login shell and must keep the TTY. Buffering it
# hides the [refract:...] prompt until that shell exits.
if [ "\${1:-}" = "use" ]; then
    exec "$DEMO_BIN/refract.py" "\$@"
fi
set +e
out="\$(mktemp)"
"$DEMO_BIN/refract.py" "\$@" >"\$out" 2>&1
code=\$?
sed "s|$DEMO_HOME|$DISPLAY_HOME|g" "\$out"
rm -f "\$out"
exit "\$code"
EOF
chmod +x "$DEMO_BIN/refract"

if [ -d "$HOST_HOME/.cache/rod" ]; then
    ln -s "$HOST_HOME/.cache/rod" "$DEMO_HOME/.cache/rod"
fi
if [ -d "$HOST_HOME/Library/Caches/pip" ]; then
    mkdir -p "$DEMO_HOME/Library/Caches"
    ln -s "$HOST_HOME/Library/Caches/pip" "$DEMO_HOME/Library/Caches/pip"
fi
if [ -d "$HOST_HOME/.cache/pip" ]; then
    ln -s "$HOST_HOME/.cache/pip" "$DEMO_HOME/.cache/pip"
fi

WHEELHOUSE="$DEMO_ROOT/wheels"
mkdir -p "$WHEELHOUSE"
python3 -m pip download django -d "$WHEELHOUSE" -q

# Login bash only reads .bash_profile. Point it at .bashrc so the
# colorway prompt hook (PROMPT_COMMAND) actually runs after `refract use`.
cat > "$DEMO_HOME/.bashrc" <<EOF
# Login bash rebuilds PATH via path_helper; put the demo CLI back.
export PATH="$DEMO_BIN:\$PATH"
export PIP_FIND_LINKS="$WHEELHOUSE"
export PIP_NO_INDEX=1
export PIP_PROGRESS_BAR=off
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_NO_INPUT=1
export CI=1
PS1="\$ "
if [ -n "\${REFRACT_ENV:-}" ] && [ -f "\$HOME/.refract/envs/\$REFRACT_ENV/bin/activate" ]; then
  VIRTUAL_ENV_DISABLE_PROMPT=1
  . "\$HOME/.refract/envs/\$REFRACT_ENV/bin/activate"
fi
pip() {
  if [ "\${1:-}" = "install" ]; then
    command pip "\$@" --no-compile --progress-bar off
    return \$?
  fi
  if [ "\${1:-}" = "show" ]; then
    command pip "\$@" 2>&1 | sed -u "s|$DEMO_HOME|$DISPLAY_HOME|g"
    return "\${PIPESTATUS[0]}"
  fi
  command pip "\$@"
}
EOF
printf '%s\n' '[ -f "$HOME/.bashrc" ] && . "$HOME/.bashrc"' > "$DEMO_HOME/.bash_profile"
cp "$DEMO_HOME/.bash_profile" "$DEMO_HOME/.profile"

export HOME="$DEMO_HOME"
export PATH="$DEMO_BIN:/usr/local/bin:/usr/bin:/bin"
export SHELL="/bin/bash"
export TERM="xterm-256color"

refract install >/dev/null

if ! grep -q 'refract prompt integration' "$HOME/.bashrc"; then
    echo "colorway snippets were not installed into the demo HOME" >&2
    exit 1
fi

cd "$ROOT"
TAPE="${1:-$ROOT/demo/refract.tape}"
vhs "$TAPE"
echo "Wrote ${TAPE%.tape}.gif"
