# Chromium-Fish MCP

A Claude Code MCP server that provides `websearch` and `webfetch` tools powered by the [ChromiumFish](https://github.com/arman-bd/chromiumfish) stealth browser (a fingerprint-hardened Chromium fork driven through Playwright).

All web research goes through one coherent, bot-resistant browser identity, which lets the search tool use Google directly instead of scraping-friendly fallback engines.

## Tools

- **`websearch(query, max_results=10)`** — runs the query in the stealth browser. Engine order: **Google first** (with bot-wall detection), then DuckDuckGo HTML, then Bing. Returns title, clean URL, and snippet per result. Ads are filtered, and Google's tracking-redirect links are resolved to the real destination domain (read from the result's visible breadcrumb, since Google obfuscates its `goto` payloads).
- **`webfetch(url)`** — loads a page in the stealth browser and returns its visible text.

## Install

Requirements: `python3`, and the `claude` CLI on your PATH.

```bash
./install.sh
```

This creates a venv at `~/.claude/chromiumfish/venv`, installs `chromiumfish[mcp]`, downloads the browser binary (`~/.cache/chromiumfish/`), symlinks the wrapper into place, links the `chromiumfish` CLI into `~/.local/bin`, and registers the server at **user scope** (`~/.claude.json`), so it loads in every Claude Code project on the machine.

### Shared install for other tools

Other tools on the machine use the same install instead of their own:

- **CLI:** `chromiumfish` on PATH (`~/.local/bin/chromiumfish`, override with `CF_BIN_DIR`). Tools find it by name, e.g. to run `chromiumfish mcp` or `chromiumfish serve`.
- **Browser:** `~/.cache/chromiumfish/<version>/<platform>/`, chromiumfish's own cache (override with `CHROMIUMFISH_CACHE_DIR`), shared by every chromiumfish install.

Restart Claude Code (or approve the new server when prompted) — the tools then appear as `mcp__chromiumfish-web__websearch` / `mcp__chromiumfish-web__webfetch`.

### Restore on a new PC

```bash
git clone <this repo> && cd chromium-fish-mcp && ./install.sh
```

That's it. Updates are `git pull` — the live install runs from a symlink to the repo file, so the repo is the single source of truth.

## Configuration

- `CF_PERSONA_SEED` — stable fingerprint persona (default `chromiumfish-web`). Change it for a fresh, unlinkable browser identity.
- The wrapper's other knobs (engine order, selectors) are in `mcp/chromiumfish_web.py`.

## Notes and limitations

- Claude Code does not allow MCP servers to override the built-in `WebSearch`/`WebFetch` tools; this server adds namespaced tools alongside them. Treat the MCP tools as the default search backend by convention.
- Google URLs are returned at domain level (e.g. `https://example.com`), because the SERP only exposes the destination cleanly in the breadcrumb. Use `webfetch` or a follow-up search to reach exact pages.
- Google aggressively bot-walls scrapers; when it does, the tool silently falls back to DuckDuckGo, then Bing.
- This repo deliberately does not contain the venv, the browser binary cache, or `~/.claude.json`.
