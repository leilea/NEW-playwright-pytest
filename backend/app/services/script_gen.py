"""Pure-function script generator: typed Step list → pytest Playwright code."""

import random
import re
import string
from datetime import datetime, timedelta
from typing import Any

OVERLAY_SELECTORS: list[str] = [
    ".comp_dialog_warp",
    ".el-dialog__wrapper",
    ".el-overlay",
    ".el-message-box__wrapper",
    ".ant-modal-wrap",
    ".v-overlay",
]


_FINGERPRINT_HELPER = '''
import json as _json
import hashlib as _hashlib
import atexit as _atexit
import time as _time
import sys as _sys
from pathlib import Path

_FINGERPRINT_FILE = Path(__file__).resolve().parent / ".fingerprints.json"
_FP_CACHE = None

def _fp_key(route: str, selector: str) -> str:
    raw = f"{route}:{selector}"[:200]
    return _hashlib.md5(raw.encode()).hexdigest()[:16]

def _fp_load():
    global _FP_CACHE
    if _FP_CACHE is not None:
        return _FP_CACHE
    try:
        if _FINGERPRINT_FILE.exists():
            data = _json.loads(_FINGERPRINT_FILE.read_text(encoding="utf-8"))
            _FP_CACHE = data.get("entries", {})
            _fp_cleanup()
        else:
            _FP_CACHE = {}
    except Exception as e:
        print(f"[fingerprint] failed to load {_FINGERPRINT_FILE}: {e}", file=_sys.stderr)
        _FP_CACHE = {}
    return _FP_CACHE

def _fp_save():
    global _FP_CACHE
    if _FP_CACHE is None:
        return
    _fp_trim()
    data = {"version": 1, "entries": dict(_FP_CACHE)}
    _FINGERPRINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        _FINGERPRINT_FILE.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[fingerprint] failed to save: {e}", file=_sys.stderr)

def _fp_cleanup():
    global _FP_CACHE
    if not _FP_CACHE:
        return
    now = _time.time()
    cutoff = now - 90 * 86400
    stale = [k for k, v in _FP_CACHE.items() if v.get("last_seen_ts", 0) < cutoff]
    for k in stale:
        del _FP_CACHE[k]
    if stale:
        print(f"[fingerprint] expired {len(stale)} stale entries", file=_sys.stderr)

def _fp_trim():
    global _FP_CACHE
    limit = 1000
    if not _FP_CACHE or len(_FP_CACHE) <= limit:
        return
    sorted_items = sorted(_FP_CACHE.items(), key=lambda x: x[1].get("last_seen_ts", 0))
    to_remove = len(_FP_CACHE) - limit
    for k, _ in sorted_items[:to_remove]:
        del _FP_CACHE[k]

def _fp_extract_attrs(locator):
    try:
        el = locator.first
        attrs = {}
        for attr in ("data-testid", "aria-label", "placeholder", "title", "id", "class"):
            val = el.get_attribute(attr)
            if val:
                attrs[attr] = val
        try:
            text = (el.inner_text() or "").strip()[:80]
            if text:
                attrs["text"] = text
        except Exception:
            pass
        try:
            tag = el.evaluate("el => el.tagName.toLowerCase()")
            if tag in ("button", "a", "input", "select", "textarea"):
                attrs["role"] = tag
        except Exception:
            pass
        return attrs if attrs else None
    except Exception:
        return None

def _fp_build_from_attrs(page, attrs: dict):
    builders = [
        ("data-testid", lambda v: page.get_by_test_id(v)),
        ("aria-label",   lambda v: page.locator(f'[aria-label="{{v}}"]'.format(v=v))),
        ("text",         lambda v: page.get_by_text(v)),
        ("placeholder",  lambda v: page.get_by_placeholder(v)),
        ("role",         lambda v: page.get_by_role(v)),
        ("id",           lambda v: page.locator(f"#{v}")),
    ]
    for _attr_name, build in builders:
        val = attrs.get(_attr_name)
        if not val:
            continue
        try:
            loc = build(val)
            if loc.count() > 0:
                return loc
        except Exception:
            continue
    return None

_atexit.register(_fp_save)


def _safe(page, strategies):
    route = ""
    try:
        route = page.url.split("?")[0] if page.url else ""
    except Exception:
        pass

    for sel in strategies[:-1]:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                if route:
                    try:
                        attrs = _fp_extract_attrs(loc)
                        if attrs:
                            entries = _fp_load()
                            key = _fp_key(route, strategies[0])
                            now = _time.time()
                            entry = entries.get(key, {"first_seen_ts": now, "hit_count": 0})
                            entry["route"] = route
                            entry["selector"] = strategies[0]
                            entry["attrs"] = attrs
                            entry["last_seen_ts"] = now
                            entry["hit_count"] = entry.get("hit_count", 0) + 1
                            entries[key] = entry
                    except Exception:
                        pass
                return page.locator(sel)
        except Exception:
            continue

    if route:
        try:
            entries = _fp_load()
            key = _fp_key(route, strategies[0])
            entry = entries.get(key)
            if entry:
                healed = _fp_build_from_attrs(page, entry.get("attrs", {}))
                if healed:
                    print(f"[fingerprint] healed: {strategies[0]}", file=_sys.stderr)
                    try:
                        attrs = _fp_extract_attrs(healed)
                        if attrs:
                            entry["attrs"] = attrs
                            entry["last_seen_ts"] = _time.time()
                            entry["hit_count"] = entry.get("hit_count", 0) + 1
                            entries[key] = entry
                    except Exception:
                        pass
                    return healed
        except Exception:
            pass

    return page.locator(strategies[-1])
'''


def _to_engine_sel(sel: str) -> str:
    if sel.startswith("__label:"):
        return f"label={sel[8:]}"
    if sel.startswith("__placeholder:"):
        return f"placeholder={sel[14:]}"
    if sel.startswith("__testid:"):
        return f"[data-testid={sel[9:]}]"
    if sel.startswith("__text:"):
        return f"text={sel[7:]}"
    if sel.startswith("__role:"):
        rest = sel[7:]
        if ":" in rest:
            r, n = rest.split(":", 1)
            return f'role={r}[name="{n}"]'
        return f"role={rest}"
    if sel.startswith("__alt:"):
        return f"[alt={sel[6:]}]"
    if sel.startswith("__title:"):
        return f"[title={sel[8:]}]"
    if sel.startswith("__xpath:"):
        return sel[8:]
    return sel


def _build_fallbacks(sel: str) -> list[str]:
    clean = sel
    if "|" in clean:
        clean = clean.split("|")[0]

    primary = _to_engine_sel(clean)
    fallbacks: list[str] = [primary]

    if sel.startswith("__role:"):
        rest = clean[7:]
        if ":" in rest:
            _r, n = rest.split(":", 1)
            if len(n) >= 2 and not n.isdigit():
                fb = f"text={n}"
                if fb != primary:
                    fallbacks.append(fb)
                fallbacks.append(f"{_r}:has-text('{n}')")
    elif sel.startswith("__text:"):
        text = clean[7:]
        if len(text) >= 2 and not text.isdigit():
            fb1 = f"[aria-label=\"{text}\"]"
            fb2 = f"button:has-text('{text}')"
            if fb1 != primary:
                fallbacks.append(fb1)
            if fb2 != primary:
                fallbacks.append(fb2)
    elif sel.startswith("__label:"):
        label = clean[8:]
        if len(label) >= 2:
            fb1 = f"placeholder={label}"
            fb2 = f"input[name=\"{label}\"]"
            if fb1 != primary:
                fallbacks.append(fb1)
            if fb2 != primary:
                fallbacks.append(fb2)
    elif sel.startswith("__placeholder:"):
        ph = clean[14:]
        if len(ph) >= 2:
            fb = f"input[placeholder*=\"{ph}\"]"
            if fb != primary:
                fallbacks.append(fb)
    elif sel.startswith("__testid:") or sel.startswith("__xpath:") or sel.startswith("__alt:") or sel.startswith("__title:"):
        pass
    else:
        has_id = re.match(r'^#[\w\-]+$', clean)
        if has_id:
            pass
        elif ":has-text(" in clean:
            m = re.search(r""":has-text\(['"]([^'"]+)['"]\)""", clean)
            if m:
                text = m.group(1)
                fb1 = f"text={text}"
                fb2 = f"button:has-text('{text}')"
                if fb1 not in fallbacks:
                    fallbacks.append(fb1)
                if fb2 not in fallbacks:
                    fallbacks.append(fb2)
        else:
            id_m = re.search(r'#([a-zA-Z\u4e00-\u9fff][\w\-]{1,})', clean)
            class_m = re.search(r'\.([a-zA-Z\u4e00-\u9fff][\w\-]{1,})', clean)
            word = None
            if id_m:
                word = id_m.group(1).replace('-', ' ').replace('_', ' ')
            elif class_m:
                word = class_m.group(1).replace('-', ' ').replace('_', ' ')
            if word and len(word) >= 2 and not word.isdigit():
                fb1 = f"text={word}"
                fb2 = f"button:has-text('{word}')"
                if fb1 not in fallbacks:
                    fallbacks.append(fb1)
                if fb2 not in fallbacks:
                    fallbacks.append(fb2)

    seen: set[str] = set()
    result: list[str] = []
    for s in fallbacks:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result


def _safe_locator_code(p: dict) -> str:
    sel = p.get("selector", "")
    strategies = _build_fallbacks(sel)
    if len(strategies) <= 1:
        return _locator(sel)
    strategy_lines = ",\n        ".join(repr(s) for s in strategies)
    return f"_safe(page, [\n        {strategy_lines},\n    ])"


def _step_has_healing(p: dict) -> bool:
    sel = p.get("selector", "")
    return len(_build_fallbacks(sel)) > 1


def generate_script(
    case_name: str,
    steps: list[dict[str, Any]],
    browser: str = "chromium",
    parameters: list[dict] | None = None,
) -> str:
    """Generate a pytest Playwright test function from a case name and step list."""
    safe_name = _sanitize(case_name)
    lines: list[str] = ["import pytest", "from playwright.sync_api import Page, expect"]

    has_interactive = any(s.get("action") in _INTERACTIVE_ACTIONS for s in steps)
    has_healing = any(
        s.get("action") in _INTERACTIVE_ACTIONS and _step_has_healing(dict(s.get("params") or s))
        for s in steps
    )
    if has_healing:
        lines.extend(["", "", _FINGERPRINT_HELPER.strip()])
    if has_interactive:
        lines.extend(["", "", _dismiss_overlays_text()])

    lines.extend(["", "", f"@pytest.mark.{browser}", f"def test_{safe_name}(page: Page):", f'    """{case_name}"""'])

    if has_interactive:
        lines.append("    _dismiss_overlays(page)")

    for i, s in enumerate(steps):
        lines.append(f"    print('__STEP_MARKER__:{i}')")
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
                lines.append("    _dismiss_overlays(page)")
                lines.append('    with page.expect_navigation(wait_until="load"):')
                lines.append(f"        {click_code}")
                continue

        handler = _HANDLERS.get(action)
        if handler:
            if action in _INTERACTIVE_ACTIONS:
                lines.append("    _dismiss_overlays(page)")
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
    return repr(str(v))


def _locator(sel: str) -> str:
    """Convert semantic selector prefix to Playwright locator expression.

    Supports two chaining formats:
      `` >> `` : semantic chain (Playwright-native) — ``__role:navigation >> __role:link:关于``
      `` > ``  : legacy CSS chain — ``#czr_daohang > __text:七嘴八舌``
    |tag suffixes are dropped for semantic selectors.
    """
    # semantic chain: "__role:navigation >> __role:link:关于"
    if " >> " in sel:
        parts = sel.split(" >> ")
        container = _raw_locator(parts[0])
        for i in range(1, len(parts)):
            child = parts[i]
            if "|" in child:
                child, _, _ = child.partition("|")
            child_loc = _raw_locator(child)
            container = f"{container}.{child_loc[len('page.'):]}"
        return container

    # legacy CSS chain: "#czr_daohang > __text:七嘴八舌"
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
    if sel.startswith("__xpath:"):
        xp = sel[8:]
        q = "'" if '"' in xp else '"'
        return f'page.locator({q}xpath={xp}{q})'
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


_INTERACTIVE_ACTIONS = {"click", "fill", "hover", "check", "uncheck", "select"}

_OVERLAY_HELPER = '''def _dismiss_overlays(page):
    for overlay_sel in {overlays}:
        overlay = page.locator(overlay_sel)
        if overlay.count() > 0 and overlay.first.is_visible():
            close_btn = overlay.locator('.el-dialog__close, .el-message-box__headerbtn, .el-icon-close, [aria-label="Close"]')
            if close_btn.count() > 0 and close_btn.first.is_visible():
                close_btn.first.click()
                page.wait_for_timeout(300)
'''


def _dismiss_overlays_text() -> str:
    return _OVERLAY_HELPER.format(overlays=repr(OVERLAY_SELECTORS))


# ---- step handlers ----

def _h_goto(p: dict) -> str:
    return f'page.goto({_quote(p["url"])})\n    {_wait_for_load_state()}'


def _h_click(p: dict, *, use_safe: bool = True) -> str:
    loc = _safe_locator_code(p) if use_safe else _locator(p["selector"])
    return f'{loc}.click()'


def _h_fill(p: dict, *, use_safe: bool = True) -> str:
    loc = _safe_locator_code(p) if use_safe else _locator(p["selector"])
    return f'{loc}.fill({_quote(p["value"])})'


def _h_expect(p: dict) -> str:
    loc = _locator(p["selector"])
    txt = p.get("text", "")
    state = p.get("state", "")
    if state:
        return _expect_state(loc, state)
    if txt:
        return f'expect({loc}).to_contain_text({_quote(txt)})'
    return f'expect({loc}).to_be_visible()'


def _h_check(p: dict, *, use_safe: bool = True) -> str:
    loc = _safe_locator_code(p) if use_safe else _locator(p["selector"])
    state = p.get("state", "check")
    if state == "uncheck":
        return f'{loc}.uncheck()'
    return f'{loc}.check()'


def _h_uncheck(p: dict, *, use_safe: bool = True) -> str:
    loc = _safe_locator_code(p) if use_safe else _locator(p["selector"])
    return f'{loc}.uncheck()'


def _h_select(p: dict, *, use_safe: bool = True) -> str:
    loc = _safe_locator_code(p) if use_safe else _locator(p["selector"])
    return f'{loc}.select_option({_quote(p["value"])})'


def _h_hover(p: dict, *, use_safe: bool = True) -> str:
    loc = _safe_locator_code(p) if use_safe else _locator(p["selector"])
    return f'{loc}.hover()'


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
