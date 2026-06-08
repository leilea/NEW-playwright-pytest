"""Pure-function script generator: typed Step list → pytest Playwright code."""

from typing import Any


def generate_script(case_name: str, steps: list[dict[str, Any]], browser: str = "chromium") -> str:
    """Generate a pytest test function from a case name and step list."""
    lines = [
        "import pytest",
        "from playwright.sync_api import Page, expect",
        "",
        "",
        f"@pytest.mark.{browser}",
        f"def test_{_sanitize(case_name)}(page: Page):",
        f'    """{case_name}"""',
    ]
    for s in steps:
        action = s.get("action", "goto")
        params = s.get("params", {})
        handler = _HANDLERS.get(action)
        if handler:
            lines.append(f"    {handler(params)}")
        else:
            lines.append(f"    # unknown action: {action} {params}")
    return "\n".join(lines) + "\n"


def _sanitize(name: str) -> str:
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in name).lower().strip("_") or "test"


def _quote(v: Any) -> str:
    s = str(v)
    return f'"{s}"' if '"' not in s else f"'{s}'"


# ---- step handlers ----

def _h_goto(p: dict) -> str:
    return f'page.goto({_quote(p["url"])})'


def _h_click(p: dict) -> str:
    return f'page.click({_quote(p["selector"])})'


def _h_fill(p: dict) -> str:
    return f'page.fill({_quote(p["selector"])}, {_quote(p["value"])})'


def _h_expect(p: dict) -> str:
    sel = _quote(p["selector"])
    txt = p.get("text", "")
    return f'expect(page.locator({sel})).to_contain_text({_quote(txt)})' if txt else f'expect(page.locator({sel})).to_be_visible()'


def _h_check(p: dict) -> str:
    state = p.get("state", "check")
    return f'page.uncheck({_quote(p["selector"])})' if state == "uncheck" else f'page.check({_quote(p["selector"])})'


def _h_select(p: dict) -> str:
    return f'page.select_option({_quote(p["selector"])}, {_quote(p["value"])})'


def _h_hover(p: dict) -> str:
    return f'page.hover({_quote(p["selector"])})'


def _h_wait(p: dict) -> str:
    return f'page.wait_for_timeout({int(p.get("ms", 1000))})'


def _h_screenshot(p: dict) -> str:
    name = p.get("name", "")
    return f'page.screenshot(path=f"screenshots/{name}.png")' if name else "page.screenshot()"


def _h_scroll(p: dict) -> str:
    x, y = p.get("x", 0), p.get("y", 0)
    return f'page.evaluate("window.scrollTo({x}, {y})")'


def _h_eval(p: dict) -> str:
    return f'page.evaluate({_quote(p["code"])})'


_HANDLERS = {
    "goto": _h_goto,
    "click": _h_click,
    "fill": _h_fill,
    "expect": _h_expect,
    "check": _h_check,
    "select": _h_select,
    "hover": _h_hover,
    "wait": _h_wait,
    "screenshot": _h_screenshot,
    "scroll": _h_scroll,
    "eval": _h_eval,
}
