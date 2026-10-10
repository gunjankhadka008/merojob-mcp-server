# MeroJob MCP Server

Let Claude Desktop search [MeroJob](https://merojob.com) (Nepal's job portal) and read full job descriptions.

Ask Claude things like:

> Search MeroJob for Data Analyst openings.
>
> Read this listing and summarize the requirements: `https://merojob.com/...`
>
> Find entry-level Data Engineer jobs and compare them with my qualifications.

---

## What you need

- A Mac (the setup script is for macOS; Windows users see [Manual setup](#manual-setup-windows-or-if-you-prefer))
- [Claude Desktop](https://claude.ai/download)
- [Python 3.10 or newer](https://www.python.org/downloads/) (check with `python3 --version`)
- Git

---

## Quick start (3 steps)

### 1. Download the project

```bash
git clone https://github.com/gunjankhadka008/merojob-mcp-server.git
cd merojob-mcp-server
```

### 2. Run setup (once)

```bash
bash setup.sh
```

This does everything for you:

- creates a virtual environment and installs the dependencies
- installs the headless browser (this step takes a minute or two)
- generates a private API key and saves it in `.env` (never committed to git)
- adds the server to Claude Desktop's config with that same key

When it says **"Setup complete!"**, fully quit Claude Desktop (**Cmd+Q**) and reopen it.

### 3. Start the server

```bash
bash start.sh
```

You should see `Uvicorn running on http://127.0.0.1:8000`. **Leave this window open** while you use Claude.

Now open Claude Desktop and try: *"Search MeroJob for <'any job role'> jobs."*

The first search takes 10 to 20 seconds because the server opens a real browser.

---

## Using it day to day

Setup is a one-time thing. After that, whenever you want to use the tools:

```bash
cd merojob-mcp-server
bash start.sh
```

Keep the terminal open, and use Claude Desktop as normal. Press **Ctrl+C** in the terminal to stop the server.

---

## If something goes wrong

| What you see | Fix |
|---|---|
| `python3: command not found` or "Python 3.10 or newer is required" | Install Python from python.org, then run `bash setup.sh` again. |
| Claude says the tool is disconnected / "Server disconnected" | You didn't restart Claude Desktop after setup. Quit it with **Cmd+Q** and reopen it. |
| Claude says `401 Unauthorized` | The server was started with a different key than Claude has. Run `bash setup.sh` again (it keeps your key and re-syncs the config), restart Claude Desktop, then run `bash start.sh`. |
| Claude says connection refused or the tool errors | The server isn't running. Run `bash start.sh` and leave it open. |
| `Port 8000 is already in use` | The server is already running in another terminal. Use that one, or stop it with Ctrl+C. |
| "Not set up yet" when running `start.sh` | Run `bash setup.sh` first. |
| Search returns nothing | Try broader keywords. The site may simply have no matching jobs. |
| 403 errors from MeroJob | The site is blocking automated traffic. Wait a while and try again, and avoid many rapid searches. |

Claude Desktop's log for this tool is at `~/Library/Logs/Claude/mcp-server-merojob-pro.log`. If you ask for help, paste the last lines of it (it never contains your key).

---

## How it works

```
You -> Claude Desktop -> proxy_mcp.py -> main.py (local server) -> merojob.com
```

- **`proxy_mcp.py`** gives Claude two tools: `search_merojob` and `get_job_description`. It forwards each request to the local server with your API key.
- **`main.py`** is a small local server. It checks the key, opens a headless browser, loads the MeroJob page, strips the clutter, and returns clean text.
- **`setup.sh` / `start.sh`** install everything and run the server so you don't have to.

---

## Security

- Every request to the server needs your private API key. The key is generated on your machine, stored in `.env`, and compared in constant time. It is never in the code.
- The server only opens `merojob.com` pages. Other addresses are rejected, so it cannot be used to browse arbitrary or internal sites.
- The server only listens on `127.0.0.1` (your own computer). Don't expose it to the internet or change it to `0.0.0.0`. A headless browser behind a public endpoint is dangerous.
- Never commit `.env` or your Claude Desktop config. Both are listed in `.gitignore`.
- If you ever leak your key, delete `.env`, run `bash setup.sh` for a new one, restart Claude Desktop, and run `bash start.sh`.

---

## Manual setup (Windows, or if you prefer)

The scripts above are for macOS. If you are on Windows or want to do it by hand:

**1. Install**

```bash
git clone https://github.com/gunjankhadka008/merojob-mcp-server.git
cd merojob-mcp-server
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
playwright install chromium
```

**2. Make a private key** and keep it somewhere safe:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**3. Add this to Claude Desktop's config** (`%APPDATA%\Claude\claude_desktop_config.json` on Windows, `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS), inside `mcpServers`, using your real paths and key:

```json
"merojob-pro": {
  "command": "C:\\path\\to\\merojob-mcp-server\\venv\\Scripts\\python.exe",
  "args": ["C:\\path\\to\\merojob-mcp-server\\proxy_mcp.py"],
  "env": { "MEROJOB_API_KEY": "paste-your-key-here" }
}
```

On macOS and Linux the command is `/path/to/merojob-mcp-server/venv/bin/python`. Keep valid JSON: commas between entries and double quotes everywhere. Then quit and reopen Claude Desktop.

**4. Start the server** with the same key, in a terminal that stays open:

```bash
# Windows PowerShell
$env:MEROJOB_API_KEY="paste-your-key-here"
uvicorn main:app --host 127.0.0.1 --port 8000

# macOS / Linux
export MEROJOB_API_KEY="paste-your-key-here"
uvicorn main:app --host 127.0.0.1 --port 8000
```

The key in the config and the key in the terminal must be identical.

---

## Project files

```text
merojob-mcp-server/
├── setup.sh           # one-time setup (macOS)
├── start.sh           # starts the local server
├── proxy_mcp.py       # MCP tools Claude calls
├── main.py            # local server + browser scraper
├── requirements.txt   # Python dependencies
├── Dockerfile         # container build (advanced)
└── README.md
```

---

## Responsible use

This project is for personal research and workflow automation. Respect MeroJob's terms of service, robots.txt guidance, and rate limits. Keep request volume low and do not try to bypass access controls.

---

## Contributing

Suggestions and fixes are welcome!

- **Found a bug or have an idea?** Open an [Issue](https://github.com/gunjankhadka008/merojob-mcp-server/issues) and describe what you expected, what happened, and how to reproduce it.
- **Want to change the code?** Fork this repo, make your change, and open a Pull Request with a short description of what it does.

Please never include API keys, `.env` files, or your Claude Desktop config in an issue or pull request.
## Author

**Gunjan Khadka**  ·  [@gunjankhadka008](https://github.com/gunjankhadka008)
