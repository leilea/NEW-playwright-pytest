import asyncio
import json
import re
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


_GET_BY_NORMALIZE = [
    (re.compile(r'page\.get_by_role\((["\'])(.+?)\1\s*,\s*name=(["\'])(.+?)\3\s*,\s*exact\s*=\s*True\s*\)'), r'page.locator("__role:\2:\4")'),
    (re.compile(r'page\.get_by_role\((["\'])(.+?)\1\s*,\s*name=(["\'])(.+?)\3\s*\)'), r'page.locator("__role:\2:\4")'),
    (re.compile(r'page\.get_by_role\((["\'])(.+?)\1\s*\)'), r'page.locator("__role:\2")'),
    (re.compile(r'page\.get_by_placeholder\((["\'])(.+?)\1\s*\)'), r'page.locator("__placeholder:\2")'),
    (re.compile(r'page\.get_by_label\((["\'])(.+?)\1\s*\)'), r'page.locator("__label:\2")'),
    (re.compile(r'page\.get_by_text\((["\'])(.+?)\1\s*,\s*exact\s*=\s*True\s*\)'), r'page.locator("__text:\2")'),
    (re.compile(r'page\.get_by_text\((["\'])(.+?)\1\s*\)'), r'page.locator("__text:\2")'),
    (re.compile(r'page\.get_by_test_id\((["\'])(.+?)\1\s*\)'), r'page.locator("__testid:\2")'),
    (re.compile(r'page\.get_by_alt_text\((["\'])(.+?)\1\s*\)'), r'page.locator("__alt:\2")'),
    (re.compile(r'page\.get_by_title\((["\'])(.+?)\1\s*\)'), r'page.locator("__title:\2")'),
]


def _normalize_codegen_line(line: str) -> str:
    for pattern, replacement in _GET_BY_NORMALIZE:
        line = pattern.sub(replacement, line)
    return line


STEP_PATTERNS = [
    ("goto", r'page\.goto\("(.*)"\)'),
    ("click", r'page\.click\("([^"]+)"\)'),
    ("click", r'page\.locator\("([^"]+)"\)(?:\.first|\.nth\(\d+\))?\.click\b'),
    ("fill", r'page\.fill\("([^"]+)",\s*"([^"]*)"'),
    ("fill", r'page\.locator\("([^"]+)"\)(?:\.first|\.nth\(\d+\))?\.fill\("([^"]*)"'),
    ("expect", r'expect\(page\.locator\("([^"]+)"\)\)\.to_contain_text\("([^"]*)"'),
    ("check", r'page\.locator\("([^"]+)"\)(?:\.first|\.nth\(\d+\))?\.(check|uncheck)'),
    ("select", r'page\.select_option\("([^"]+)",\s*"([^"]*)"'),
    ("select", r'page\.locator\("([^"]+)"\)(?:\.first|\.nth\(\d+\))?\.select_option\("([^"]*)"'),
    ("hover", r'page\.locator\("([^"]+)"\)(?:\.first|\.nth\(\d+\))?\.hover'),
    ("wait", r'page\.wait_for_timeout\((\d+)\)'),
    ("screenshot", r'page\.screenshot'),
    ("scroll", r'page\.evaluate\("window\.scrollTo\((\d+),\s*(\d+)\)"'),
    ("eval", r'page\.evaluate\("(.*)"'),
]


def parse_codegen_line(line: str) -> dict | None:
    line = _normalize_codegen_line(line)
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
