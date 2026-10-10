#!/usr/bin/env bash
# One-time setup for the MeroJob MCP server.
# Run with:  bash setup.sh
set -e
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

say()  { printf "\n==> %s\n" "$1"; }
fail() { printf "\nERROR: %s\n" "$1" >&2; exit 1; }

# 1. Check Python ---------------------------------------------------------
PYTHON="$(command -v python3 || true)"
[ -z "$PYTHON" ] && fail "python3 was not found. Install Python 3.10 or newer from https://www.python.org/downloads/ and run this again."
"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || fail "Python 3.10 or newer is required (you have: $("$PYTHON" -V 2>&1))."

# 2. Virtual environment + dependencies -----------------------------------
if [ ! -d venv ]; then
  say "Creating virtual environment"
  "$PYTHON" -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate

say "Installing dependencies"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
python -c "import fastmcp" 2>/dev/null || pip install --quiet fastmcp

say "Installing the headless browser (Chromium). This can take a minute..."
playwright install chromium

# 3. Private API key (stored in .env, which git ignores) -------------------
if [ -f .env ] && grep -q '^MEROJOB_API_KEY=' .env; then
  say "Keeping the existing API key in .env"
else
  say "Generating a private API key"
  KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
  ( umask 077; printf 'MEROJOB_API_KEY=%s\n' "$KEY" > .env )
fi

# 4. Connect Claude Desktop (macOS) -----------------------------------------
say "Connecting Claude Desktop"
PROJECT_DIR="$PROJECT_DIR" python - <<'PY'
import json, os, shutil, sys

project = os.environ["PROJECT_DIR"]

key = None
with open(os.path.join(project, ".env")) as f:
    for line in f:
        if line.startswith("MEROJOB_API_KEY="):
            key = line.strip().split("=", 1)[1]
if not key:
    sys.exit("Could not read the key from .env")

if sys.platform != "darwin":
    print("NOTE: automatic Claude Desktop setup only supports macOS.")
    print("      Follow 'Manual setup' in the README to connect Claude Desktop.")
    sys.exit(0)

cfg_dir = os.path.expanduser("~/Library/Application Support/Claude")
path = os.path.join(cfg_dir, "claude_desktop_config.json")
os.makedirs(cfg_dir, exist_ok=True)

cfg = {}
if os.path.exists(path) and os.path.getsize(path) > 0:
    shutil.copy(path, path + ".backup")
    try:
        with open(path) as f:
            cfg = json.load(f)
    except json.JSONDecodeError:
        sys.exit(
            "Your Claude Desktop config file is not valid JSON.\n"
            "A copy was saved next to it as claude_desktop_config.json.backup.\n"
            "Fix or delete the file, then run: bash setup.sh"
        )

cfg.setdefault("mcpServers", {})["merojob-pro"] = {
    "command": os.path.join(project, "venv", "bin", "python"),
    "args": [os.path.join(project, "proxy_mcp.py")],
    "env": {"MEROJOB_API_KEY": key},
}

with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
print("Claude Desktop config updated.")
PY

cat <<'DONE'

==> Setup complete!

Next steps:
  1. Quit Claude Desktop completely (Cmd+Q) and reopen it.
  2. Start the server in this terminal:   bash start.sh
  3. In Claude Desktop, ask: "Search MeroJob for Data Analyst jobs"
DONE
