import asyncio
import json
from typing import AsyncIterator

async def start_codegen(target_url: str) -> AsyncIterator[dict]:
    """Launch playwright codegen and yield parsed step events."""
    proc = await asyncio.create_subprocess_exec(
        "playwright", "codegen", "--target=python",
        target_url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        async for line in proc.stdout:
            text = line.decode(errors="replace").strip()
            if not text:
                continue
            step = parse_codegen_line(text)
            if step:
                yield step
    finally:
        if proc.returncode is None:
            proc.terminate()
            await proc.wait()


STEP_PATTERNS = [
    ("goto", r'page\.goto\("(.*)"\)'),
    ("click", r'page\.(?:click|locator)\("([^"]+)"\)\.click\b'),
    ("fill", r'page\.(?:fill|locator)\("([^"]+)"\)\.fill\("([^"]*)"'),
    ("expect", r'expect\(page\.locator\("([^"]+)"\)\)\.to_contain_text\("([^"]*)"'),
    ("check", r'page\.locator\("([^"]+)"\)\.(check|uncheck)'),
    ("select", r'page\.(?:select_option|locator)\("([^"]+)"\)\.select_option\("([^"]*)"'),
    ("hover", r'page\.locator\("([^"]+)"\)\.hover'),
    ("wait", r'page\.wait_for_timeout\((\d+)\)'),
    ("screenshot", r'page\.screenshot'),
    ("scroll", r'page\.evaluate\("window\.scrollTo\((\d+),\s*(\d+)\)"'),
    ("eval", r'page\.evaluate\("(.*)"'),
]


def parse_codegen_line(line: str) -> dict | None:
    import re
    for action, pattern in STEP_PATTERNS:
        m = re.search(pattern, line)
        if not m:
            continue
        params: dict = {}
        if action == "goto":
            params["url"] = m.group(1).replace('\\"', '"')
        elif action == "click":
            params["selector"] = m.group(1).replace('\\"', '"')
        elif action == "fill":
            params["selector"] = m.group(1).replace('\\"', '"')
            params["value"] = m.group(2)
        elif action == "expect":
            params["selector"] = m.group(1).replace('\\"', '"')
            params["text"] = m.group(2)
        elif action == "check":
            params["selector"] = m.group(1).replace('\\"', '"')
            params["state"] = m.group(2)
        elif action == "select":
            params["selector"] = m.group(1).replace('\\"', '"')
            params["value"] = m.group(2)
        elif action == "hover":
            params["selector"] = m.group(1).replace('\\"', '"')
        elif action == "wait":
            params["ms"] = int(m.group(1))
        elif action == "screenshot":
            params["name"] = ""
        elif action == "scroll":
            params["x"] = int(m.group(1))
            params["y"] = int(m.group(2))
        elif action == "eval":
            params["code"] = m.group(1).replace('\\"', '"')
        return {"action": action, "params": params}
    return None
