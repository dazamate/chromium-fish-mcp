#!/usr/bin/env python3
"""ChromiumFish-backed WebSearch/WebFetch MCP server.

Exposes search/fetch-shaped tools powered by the ChromiumFish stealth
browser (fingerprint-hardened Chromium driven through Playwright), so web
research goes through one coherent, bot-resistant browser identity.

Search engine order: Google first (with bot-wall detection), then
DuckDuckGo HTML, then Bing.

Register in .mcp.json as:
    {"command": "<venv>/bin/python", "args": ["mcp/chromiumfish_web.py"]}

Optional env vars:
    CF_PERSONA_SEED  stable fingerprint persona (default "chromiumfish-web")
"""

from __future__ import annotations

import os
import urllib.parse

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("chromiumfish-web")

SEED = os.environ.get("CF_PERSONA_SEED", "chromiumfish-web")

_browser_ctx = None
_browser = None
_page = None


async def _get_page():
    """Lazily launch the ChromiumFish browser and return one shared page."""
    global _browser_ctx, _browser, _page
    if _page is None:
        from chromiumfish.async_api import AsyncChromiumfish

        _browser_ctx = AsyncChromiumfish(persona_seed=SEED, headless=True)
        _browser = await _browser_ctx.__aenter__()
        _page = await _browser.new_page()
    return _page


async def _visible_text(page):
    try:
        return await page.inner_text("body")
    except Exception:
        return await page.locator("body").inner_text()


@mcp.tool()
async def websearch(query: str, max_results: int = 10) -> str:
    """Search the web for `query` in the stealth browser.

    Returns result titles with their URLs, plus snippets. Tries Google
    first (skips it if a bot-wall interstitial appears), then DuckDuckGo,
    then Bing. Best-effort: if structured extraction fails, returns the
    results page's visible text.
    """
    page = await _get_page()
    q = urllib.parse.quote(query)
    engines = [
        ("google", f"https://www.google.com/search?q={q}&hl=en&gl=us&num=20"),
        ("duckduckgo", f"https://html.duckduckgo.com/html/?q={q}"),
        ("bing", f"https://www.bing.com/search?q={q}"),
    ]
    last_err = None
    for name, url in engines:
        try:
            await page.goto(url, timeout=45000)
            await page.wait_for_load_state("domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1200)
            if name == "google":
                # Google walls bots with a "not a robot" interstitial; skip it.
                title = (await page.title() or "").lower()
                body_head = ((await _visible_text(page)) or "")[:2000].lower()
                if "not a robot" in title or "unusual traffic" in body_head:
                    continue
                raw_links = await page.eval_on_selector_all(
                    "#search h3",
                    """els => els.map(e => {
                        const t = (e.innerText || '').trim();
                        let node = e;
                        let cite = null;
                        while (node && node !== document.body) {
                            node = node.parentElement;
                            if (node) { cite = node.querySelector('cite'); if (cite) break; }
                        }
                        let u = '';
                        if (cite) {
                            const m = (cite.textContent || '').match(/^(https?:\\/\\/[^\\s›»>]+)/);
                            if (m) u = m[1];
                        }
                        return {t, u};
                    })""",
                )
                links = [l for l in raw_links if l.get("u")]
                if len(links) < 2:
                    continue
                snips = await page.eval_on_selector_all(
                    "div.VwiC3b, span.aCOpRe",
                    "els => els.map(e => (e.innerText || '').trim())",
                )
            elif name == "duckduckgo":
                raw_links = await page.eval_on_selector_all(
                    "a.result__a",
                    """els => els.map(e => {
                        let u = e.href;
                        const m = u.match(/[?&]uddg=([^&]+)/);
                        if (m) { try { u = decodeURIComponent(m[1]); } catch (_) {} }
                        return {t: (e.innerText || '').trim(), u, ad: !!e.closest('.result--ad')};
                    })""",
                )
                links = [l for l in raw_links if not l.get("ad")]
                snips = await page.eval_on_selector_all(
                    ".result__snippet",
                    "els => els.map(e => (e.innerText || '').trim())",
                )
            else:
                links = await page.eval_on_selector_all(
                    "h2 a",
                    "els => els.map(e => ({t: (e.innerText || '').trim(), u: e.href}))",
                )
                snips = await page.eval_on_selector_all(
                    ".b_caption p, .b_caption",
                    "els => els.map(e => (e.innerText || '').trim())",
                )
            if links:
                out = []
                for i, item in enumerate(links[: max(1, max_results)]):
                    snip = snips[i] if i < len(snips) else ""
                    out.append(f"{i + 1}. {item['t']}\n   {item['u']}\n   {snip}")
                return "\n\n".join(out).strip()
            if name == "google":
                # No parseable results on Google = likely a wall; don't return junk.
                continue
            text = (await _visible_text(page) or "").strip()
            if len(text) > 60:
                return text[:12000]
        except Exception as exc:  # fall through to the next engine
            last_err = exc
            continue
    return f"websearch failed on all engines ({last_err})"


@mcp.tool()
async def webfetch(url: str) -> str:
    """Fetch a URL in the stealth browser and return the page's visible text."""
    page = await _get_page()
    try:
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("domcontentloaded", timeout=30000)
        return (await _visible_text(page) or "").strip()[:30000]
    except Exception as exc:
        return f"webfetch failed: {exc}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
