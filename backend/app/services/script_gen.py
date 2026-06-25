"""Pure-function script generator: typed Step list → pytest Playwright code."""

import random
import string
from datetime import datetime, timedelta
from typing import Any


def generate_script(
    case_name: str,
    steps: list[dict[str, Any]],
    browser: str = "chromium",
    breadcrumb: bool = False,
    breadcrumb_id: str = "",
    parameters: list[dict] | None = None,
) -> str:
    """Generate a pytest test function from a case name and step list.

    When *breadcrumb* is True, the generated script wraps ``page`` with
    ``crumb()`` so that locator failures are automatically healed via
    element fingerprint matching.
    """
    safe_name = _sanitize(case_name)
    test_id = breadcrumb_id or case_name
    lines: list[str] = ["import pytest", "from playwright.sync_api import Page, expect"]
    if breadcrumb:
        lines.append("from breadcrumb import crumb")
    lines.extend(["", "", f"@pytest.mark.{browser}", f"def test_{safe_name}(page: Page):", f'    """{case_name}"""'])
    if breadcrumb:
        lines.append(f"    page = crumb(page, test_id={_quote(test_id)})")
    for i, s in enumerate(steps):
        action = s.get("action", "goto")
        params = dict(s.get("params") or s)
        if parameters:
            for k in list(params.keys()):
                if isinstance(params[k], str):
                    params[k] = replace_params(params[k], parameters)

        # click that triggered page navigation — wrap in expect_navigation to wait for AJAX
        if action == "click" and i + 1 < len(steps):
            next_step = steps[i + 1]
            if next_step.get("action") == "goto":
                click_code = _h_click(params)
                lines.append('    with page.expect_navigation(wait_until="load"):')
                lines.append(f"        {click_code}")
                continue

        handler = _HANDLERS.get(action)
        if handler:
            lines.append(f"    {handler(params)}")
        else:
            lines.append(f"    # unknown action: {action} {params}")
    return "\n".join(lines) + "\n"


def _sanitize(name: str) -> str:
    return "".join(c if c.isascii() and (c.isalnum() or c in "_-") else "_" for c in name).lower().strip("_") or "test"


def replace_params(text: str, parameters: list[dict]) -> str:
    if not text:
        return text
    for p in parameters:
        key = p.get("key", "")
        value = p.get("value", "")
        if not key:
            continue
        text = text.replace("{{" + key + "}}", value)
        import re
        text = re.sub(r"(?<!\w)" + re.escape(key) + r"(?!\w)", value, text)
    text = _resolve_builtin(text)
    return text


def _resolve_builtin(text: str) -> str:
    import re
    now = datetime.now()

    def _random(m):
        n = int(m.group(1)) if m.group(1) else 6
        return "".join(random.choices(string.digits, k=n))
    text = re.sub(r"\{\{random:(\d+)\}\}", _random, text)

    def _random_str(m):
        n = int(m.group(1)) if m.group(1) else 8
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))
    text = re.sub(r"\{\{randomStr:(\d+)\}\}", _random_str, text)

    text = text.replace("{{date}}", now.strftime("%Y-%m-%d"))
    text = text.replace("{{time}}", now.strftime("%H:%M"))
    text = text.replace("{{datetime}}", now.strftime("%Y-%m-%d %H:%M"))
    text = text.replace("{{timestamp}}", str(int(now.timestamp() * 1000)))

    def _time_add(m):
        n = int(m.group(1))
        t = now + timedelta(hours=n)
        return t.strftime("%H:%M")
    text = re.sub(r"\{\{timeAdd:h\+(\d+)\}\}", _time_add, text)

    def _time_sub(m):
        n = int(m.group(1))
        t = now - timedelta(hours=n)
        return t.strftime("%H:%M")
    text = re.sub(r"\{\{timeSub:h\+(\d+)\}\}", _time_sub, text)

    def _date_add(m):
        n = int(m.group(1))
        d = now + timedelta(days=n)
        return d.strftime("%Y-%m-%d")
    text = re.sub(r"\{\{dateAdd:d\+(\d+)\}\}", _date_add, text)

    def _date_sub(m):
        n = int(m.group(1))
        d = now - timedelta(days=n)
        return d.strftime("%Y-%m-%d")
    text = re.sub(r"\{\{dateSub:d\+(\d+)\}\}", _date_sub, text)

    return text


def _quote(v: Any) -> str:
    s = str(v)
    return f'"{s}"' if '"' not in s else f"'{s}'"


def _locator(sel: str) -> str:
    """Convert semantic selector prefix to Playwright locator expression.

    Supports chained disambiguation: ``parent > semanticSelector``.
    |tag suffixes are dropped for semantic selectors.
    """
    # chained disambiguation: "#czr_daohang > __text:七嘴八舌"
    if " > " in sel:
        parts = sel.split(" > ")
        container = _locator(parts[0])
        for i in range(1, len(parts)):
            child = parts[i]
            if "|" in child:
                child, _, _ = child.partition("|")
            child_loc = _raw_locator(child)
            container = f'{container}.{child_loc[5:]}'
        return container

    tag = None
    if "|" in sel:
        sel, _, tag = sel.partition("|")

    base = _raw_locator(sel)

    # semantic selectors (__*) are self-scoping; |tag wrapping adds noise
    if tag and sel.startswith("__"):
        return base

    if tag:
        return f'page.locator({_quote(tag)}).filter(has={base})'
    return base


def _raw_locator(sel: str) -> str:
    """Generate the Playwright locator expression sans tag-filter wrapper."""
    if sel.startswith("__label:"):
        return f'page.get_by_label({_quote(sel[8:])})'
    if sel.startswith("__placeholder:"):
        return f'page.get_by_placeholder({_quote(sel[14:])})'
    if sel.startswith("__testid:"):
        return f'page.get_by_test_id({_quote(sel[9:])})'
    if sel.startswith("__role:"):
        rest = sel[7:]
        if ":" in rest:
            r, n = rest.split(":", 1)
            return f'page.get_by_role({_quote(r)}, name={_quote(n)}, exact=True)'
        return f'page.get_by_role({_quote(rest)})'
    if sel.startswith("__text:"):
        return f'page.get_by_text({_quote(sel[7:])}, exact=True)'
    if sel.startswith("__alt:"):
        return f'page.get_by_alt_text({_quote(sel[6:])})'
    if sel.startswith("__title:"):
        return f'page.get_by_title({_quote(sel[8:])})'
    return f'page.locator({_quote(sel)})'


def _wait_for_load_state(state: str = "load") -> str:
    return f'page.wait_for_load_state({_quote(state)})'


def _expect_state(loc: str, state: str) -> str:
    state_map = {
        "hidden": "to_be_hidden",
        "enabled": "to_be_enabled",
        "disabled": "to_be_disabled",
        "editable": "to_be_editable",
        "visible": "to_be_visible",
    }
    method = state_map.get(state, "to_be_visible")
    return f'expect({loc}).{method}()'


# ---- step handlers ----

def _h_goto(p: dict) -> str:
    return f'page.goto({_quote(p["url"])})\n    {_wait_for_load_state()}'


def _h_click(p: dict) -> str:
    return f'{_locator(p["selector"])}.click()'


def _h_fill(p: dict) -> str:
    return f'{_locator(p["selector"])}.fill({_quote(p["value"])})'


def _h_expect(p: dict) -> str:
    loc = _locator(p["selector"])
    txt = p.get("text", "")
    state = p.get("state", "")
    if state:
        return _expect_state(loc, state)
    if txt:
        return f'expect({loc}).to_contain_text({_quote(txt)})'
    return f'expect({loc}).to_be_visible()'


def _h_check(p: dict) -> str:
    state = p.get("state", "check")
    if state == "uncheck":
        return f'{_locator(p["selector"])}.uncheck()'
    return f'{_locator(p["selector"])}.check()'


def _h_uncheck(p: dict) -> str:
    return f'{_locator(p["selector"])}.uncheck()'


def _h_select(p: dict) -> str:
    return f'{_locator(p["selector"])}.select_option({_quote(p["value"])})'


def _h_hover(p: dict) -> str:
    return f'{_locator(p["selector"])}.hover()'


def _h_wait(p: dict) -> str:
    return f'page.wait_for_timeout({int(p.get("ms", 1000))})'


def _h_wait_for_load_state(p: dict) -> str:
    state = p.get("state", "load")
    return _wait_for_load_state(state)


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
    "uncheck": _h_uncheck,
    "select": _h_select,
    "hover": _h_hover,
    "wait": _h_wait,
    "wait_for_load_state": _h_wait_for_load_state,
    "screenshot": _h_screenshot,
    "scroll": _h_scroll,
    "eval": _h_eval,
}
