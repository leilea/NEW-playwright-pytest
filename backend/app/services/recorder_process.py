"""Standalone recorder subprocess — communicates via stdin/stdout JSON lines.

Stdin commands: {"cmd":"stop"}

Step events are captured via dual paths:
1. console.log (real-time) → handle_console() → _emit_step()
2. window.__dsep_queue (fallback) → flush_queue() → _emit_step()
Sequence numbers (seq) deduplicate between the two paths.

Stdout events:  {"event":"started","url":"..."}
                {"event":"step","step":{...}}
                {"event":"error","message":"..."}
                {"event":"done"}
"""

import os
import sys
import json
import threading
import time
import traceback

# MUST set policy BEFORE any Playwright import
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.sync_api import sync_playwright

RECORDER_INJECT_JS = """
(() => {
    if (window.__dsep_recorder_active) return;
    window.__dsep_recorder_active = true;

    window.__dsep_queue = window.__dsep_queue || [];
    window.__dsep_seq = window.__dsep_seq || 0;

    function _countAttr(attr, value) {
        var c = 0;
        try {
            var q = value.indexOf('"') >= 0 ? "'" : '"';
            c = (document.querySelectorAll('[' + attr + '=' + q + value + q + ']') || []).length;
        } catch(e) { c = 999; }
        return c;
    }

    function genSelector(el) {
        if (!el || el === document) return 'body';

        var lbl = _findLabel(el);
        var aria = el.getAttribute('aria-label');
        var role = _inferRole(el);
        var aname = aria || (el.textContent || '').trim().slice(0, 80) || '';
        var txt = (el.textContent || '').trim().slice(0, 60);
        var tag = el.tagName.toLowerCase();
        var alt = el.getAttribute('alt');
        var title = el.getAttribute('title');
        var ph = el.getAttribute('placeholder');

        function _scope(sel) {
            if (tag === 'div' || tag === 'span' || tag === 'body' || tag === 'html') return sel;
            return sel + '|' + tag;
        }

        // === Phase 1: Collect all semantic candidates with preference ===
        var candidates = [];

        // (pref=10) data-testid — test-only attribute, most stable
        var tid = el.getAttribute('data-testid');
        if (tid) {
            candidates.push({sel: '__testid:' + tid, pref: 10, unique: _countAttr('data-testid', tid) <= 1});
        }

        // (pref=9) title — HTML metadata, stable across UI changes
        if (title) {
            candidates.push({sel: '__title:' + title, pref: 9, unique: _countAttr('title', title) <= 1});
        }

        // (pref=9) alt — image alt text
        if (alt && tag === 'img') {
            candidates.push({sel: '__alt:' + alt, pref: 9, unique: _countAttr('alt', alt) <= 1});
        }

        // (pref=8) label — form element label
        if (lbl) {
            candidates.push({sel: _scope('__label:' + lbl), pref: 8, unique: true});
        }

        // (pref=8) placeholder — input hint
        if (ph) {
            candidates.push({sel: _scope('__placeholder:' + ph), pref: 8, unique: _countAttr('placeholder', ph) <= 1});
        }

        // (pref=7) role + aria-label
        if (role && aria) {
            candidates.push({sel: _scope('__role:' + role + ':' + aria), pref: 7, unique: _countRoleMatches(role, aria) <= 1});
        }

        // (pref=6) role + label name
        if (role && lbl) {
            candidates.push({sel: _scope('__role:' + role + ':' + lbl), pref: 6, unique: _countRoleMatches(role, lbl) <= 1});
        }

        // (pref=5) role + text name
        if (role && aname) {
            candidates.push({sel: _scope('__role:' + role + ':' + aname), pref: 5, unique: _countRoleMatches(role, aname) <= 1});
        }

        // (pref=4) role only — no accessible name
        if (role && !lbl && !aria && !ph && !aname) {
            candidates.push({sel: _scope('__role:' + role), pref: 4, unique: _countRoleMatches(role, '') <= 1});
        }

        // (pref=5) text — visible text, unique check
        if (txt) {
            var sameText = 0;
            var cs = document.querySelectorAll('a,button,input,textarea,select,em,strong,span,li,label,h1,h2,h3,h4,[onclick],[role]');
            for (var i = 0; i < cs.length && sameText < 2; i++) {
                if ((cs[i].textContent || '').trim().slice(0, 60) === txt) sameText++;
            }
            candidates.push({sel: _scope('__text:' + txt), pref: 5, unique: sameText <= 1});
        }

        // === Phase 2: Sort by preference desc, pick first unique ===
        candidates.sort(function(a, b) { return b.pref - a.pref; });

        for (var k = 0; k < candidates.length; k++) {
            if (candidates[k].unique) return candidates[k].sel;
        }

        // === Phase 3: No unique semantic — try chain with semantic parent ===
        if (candidates.length > 0) {
            var best = candidates[0];
            var semParent = _findSemanticParent(el);
            if (semParent) {
                var cleanChild = best.sel;
                var pipeIdx = cleanChild.indexOf('|');
                if (pipeIdx > -1) cleanChild = cleanChild.substring(0, pipeIdx);
                return semParent + ' >> ' + cleanChild;
            }
            // fallback: old parent context (data-testid / id / class)
            var cssParent = _findParentContext(el);
            if (cssParent) return cssParent + ' > ' + best.sel;
            // ultimate fallback: element's own id as parent context (e.g. #el-id-4667-98 > __placeholder:请输入|input)
            if (el.id && !/^\\d/.test(el.id)) return '#' + CSS.escape(el.id) + ' > ' + best.sel;
        }

        // === Phase 4: Tier 2 — CSS / attribute fallback ===

        // id — stable if not numeric
        if (el.id && !/^\\d/.test(el.id)) return '#' + CSS.escape(el.id);

        // name attribute
        var nm = el.getAttribute('name');
        if (nm) return tag + '[name="' + nm + '"]';

        // title as CSS attribute (non-unique title still better than nth-child)
        if (title) return tag + '[title="' + title + '"]';

        // discover any other unique attribute (e.g. aria-*, href, type, data-*)
        var atts = el.attributes;
        for (var j = 0; j < atts.length; j++) {
            var a = atts[j];
            var an = a.name;
            if (an === 'class' || an === 'id' || an === 'style' || an === 'data-testid' ||
                an === 'title' || an === 'name' || an === 'alt' || an === 'placeholder') continue;
            if (an.indexOf('data-') === 0) continue;
            if (a.value && _countAttr(an, a.value) <= 1) return tag + '[' + an + '="' + a.value + '"]';
        }

        // CSS class — single unique class or combined
        if (el.className && typeof el.className === 'string') {
            var cls = el.className.split(/\\s+/).filter(Boolean).join('.');
            if (cls && cls.length < 60) return tag + '.' + cls;
        }

        // === Phase 5: Tier 3 — XPath / bare tag ===
        var xp = _getXPath(el);
        if (xp) return '__xpath:' + xp;

        return tag;
    }

    function _findLabel(el) {
        const lb = el.getAttribute('aria-labelledby');
        if (lb) {
            const le = document.getElementById(lb);
            if (le && le.textContent.trim()) return le.textContent.trim();
        }
        if (el.labels && el.labels.length > 0) {
            const t = el.labels[0].textContent.trim();
            if (t) return t;
        }
        let p = el.parentElement;
        for (var i = 0; i < 5 && p; i++) {
            if (p.tagName === 'LABEL') {
                const t = p.textContent.replace(el.textContent || '', '').trim();
                if (t) return t;
                break;
            }
            p = p.parentElement;
        }
        var formItem = el.closest('.el-form-item');
        if (formItem) {
            var elLabel = formItem.querySelector('.el-form-item__label');
            if (elLabel && elLabel.textContent.trim()) return elLabel.textContent.trim();
        }
        return null;
    }

    function _inferRole(el) {
        var r = el.getAttribute('role');
        if (r) return r;
        var tag = el.tagName.toLowerCase();
        if (tag === 'button' || (tag === 'input' && ['submit','button','reset'].indexOf(el.type) >= 0)) return 'button';
        if (tag === 'a' && el.href) return 'link';
        if (tag === 'h1' || tag === 'h2' || tag === 'h3') return 'heading';
        if (tag === 'h4' || tag === 'h5' || tag === 'h6') return 'heading';
        if (tag === 'input' && el.type === 'text') return 'textbox';
        if (tag === 'textarea') return 'textbox';
        if (tag === 'select') return 'combobox';
        if (tag === 'input' && el.type === 'checkbox') return 'checkbox';
        if (tag === 'input' && el.type === 'radio') return 'radio';
        // structural roles — for chain locator disambiguation
        if (tag === 'nav') return 'navigation';
        if (tag === 'main') return 'main';
        if (tag === 'header') return 'banner';
        if (tag === 'footer') return 'contentinfo';
        if (tag === 'aside') return 'complementary';
        if (tag === 'form') return 'form';
        if (tag === 'table') return 'table';
        if (tag === 'ul' || tag === 'ol') return 'list';
        if (tag === 'li') return 'listitem';
        if (tag === 'article') return 'article';
        return null;
    }

    function _countRoleMatches(role, name) {
        var count = 0, nameLower = name.toLowerCase();
        var list = document.querySelectorAll('a,button,input,textarea,select,[role]');
        for (var i = 0; i < list.length && count < 2; i++) {
            var el = list[i];
            if (_inferRole(el) !== role) continue;
            var n = ((el.getAttribute('aria-label') || el.getAttribute('title') || (el.textContent || '').trim().slice(0, 80)) || '').toLowerCase();
            if (n === nameLower) count++;
        }
        return count;
    }

    function _findParentContext(el) {
        var p = el.parentElement, depth = 0;
        while (p && p !== document.body && depth < 4) {
            var tid = p.getAttribute('data-testid');
            if (tid) return '__testid:' + tid;
            if (p.id && !/^\\d/.test(p.id)) return '#' + CSS.escape(p.id);
            if (p.className && typeof p.className === 'string') {
                var cls = p.className.split(/\\s+/).filter(Boolean).join('.');
                if (cls && document.querySelectorAll(p.tagName.toLowerCase() + '.' + cls).length === 1)
                    return p.tagName.toLowerCase() + '.' + cls;
            }
            p = p.parentElement;
            depth++;
        }
        return null;
    }

    function _findSemanticParent(el) {
        var p = el.parentElement, depth = 0;
        while (p && p !== document.body && depth < 5) {
            var r = _inferRole(p);
            if (r) {
                var tid2 = p.getAttribute('data-testid');
                if (tid2 && _countAttr('data-testid', tid2) <= 1) return '__testid:' + tid2;
                var pname = p.getAttribute('aria-label') || (p.textContent || '').trim().slice(0, 80) || '';
                var plbl = _findLabel(p);
                if (plbl && _countRoleMatches(r, plbl) <= 1) return '__role:' + r + ':' + plbl;
                if (pname && _countRoleMatches(r, pname) <= 1) return '__role:' + r + ':' + pname;
                return '__role:' + r;
            }
            p = p.parentElement;
            depth++;
        }
        return null;
    }

    function _getXPath(el) {
        if (el.id) return '//*[@id="' + el.id + '"]';
        var parts = [];
        var cur = el;
        while (cur && cur !== document.documentElement) {
            var t = cur.tagName.toLowerCase();
            var parent = cur.parentElement;
            if (parent) {
                var sibs = parent.querySelectorAll(':scope > ' + t);
                if (sibs.length === 1) {
                    parts.unshift(t);
                } else {
                    for (var idx = 0; idx < sibs.length; idx++) {
                        if (sibs[idx] === cur) { parts.unshift(t + '[' + (idx + 1) + ']'); break; }
                    }
                }
            } else {
                parts.unshift(t);
            }
            cur = parent;
        }
        return parts.length ? '//' + parts.join('/') : null;
    }

    function rec(action, params) {
        const seq = ++window.__dsep_seq;
        const step = {seq, action, params};
        window.__dsep_queue.push(step);
        console.log('__DSEP__' + JSON.stringify(step));
    }

    document.addEventListener('click', (e) => {
        const el = e.target;
        if (el.closest('[data-dsep-ignore]')) return;
        rec('click', {selector: genSelector(el)});
    }, true);

    const fillTimers = new Map();
    function _doFill(el) {
        clearTimeout(fillTimers.get(el));
        const val = (el.value || el.textContent || '').trim();
        if (val) rec('fill', {selector: genSelector(el), value: val});
        fillTimers.delete(el);
    }
    function _resetFillTimer(el) {
        if (!el.matches || !el.matches('input:not([type=checkbox]):not([type=radio]),textarea,[contenteditable]')) return;
        if (el.closest('[data-dsep-ignore]')) return;
        clearTimeout(fillTimers.get(el));
        fillTimers.set(el, setTimeout(() => _doFill(el), 2000));
    }
    document.addEventListener('input', (e) => {
        if (e.isComposing) return;
        _resetFillTimer(e.target);
    }, true);
    document.addEventListener('blur', (e) => {
        const el = e.target;
        if (el.matches && el.matches('input:not([type=checkbox]):not([type=radio]),textarea,[contenteditable]')) {
            if (el.closest('[data-dsep-ignore]')) return;
            if (fillTimers.has(el)) _doFill(el);
        }
    }, true);

    document.addEventListener('change', (e) => {
        const el = e.target;
        if (el.tagName === 'SELECT') {
            rec('select', {selector: genSelector(el), value: el.value});
        } else if (el.type === 'checkbox') {
            rec(el.checked ? 'check' : 'uncheck', {selector: genSelector(el)});
        } else if (el.type === 'radio' && el.checked) {
            rec('check', {selector: genSelector(el)});
        }
    }, true);

    window.addEventListener('popstate', () => {
        rec('goto', {url: location.href});
    });

    const origPushState = history.pushState;
    history.pushState = function() {
        origPushState.apply(this, arguments);
        setTimeout(() => rec('goto', {url: location.href}), 100);
    };
    const origReplaceState = history.replaceState;
    history.replaceState = function() {
        origReplaceState.apply(this, arguments);
        setTimeout(() => rec('goto', {url: location.href}), 100);
    };
})();
"""


def emit(data: dict):
    """Write a JSON line to stdout, ensuring atomic output."""
    line = json.dumps(data, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def main():
    sys.stderr.write(f"STARTUP: sys.stdout.encoding={sys.stdout.encoding} py={sys.version} platform={sys.platform}\n")
    sys.stderr.flush()
    target_url = os.environ.get("RECORDER_URL", "")
    if not target_url:
        emit({"event": "error", "message": "未提供目标 URL，请先输入 URL 后再开始录制"})
        sys.exit(1)
    emit({"event": "started", "url": target_url})

    stop_event = threading.Event()

    # Read commands from stdin in a daemon thread
    def stdin_reader():
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                try:
                    cmd = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if cmd.get("cmd") == "stop":
                    stop_event.set()
                    break
        except (OSError, IOError):
            pass

    reader_thread = threading.Thread(target=stdin_reader, daemon=True)
    reader_thread.start()

    try:
        if os.environ.get("RECORDER_INSPECTOR", "false").lower() == "true":
            os.environ["PWDEBUG"] = "1"
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=os.environ.get("RECORDER_HEADLESS", "false").lower() == "true",
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
            )
            context.add_init_script(RECORDER_INJECT_JS)

            _emitted_set = set()
            _emitted_order = []
            _MAX_DEDUP = 50
            _all_pages = []

            def _emit_step(step: dict):
                content = json.dumps({k: v for k, v in step.items() if k != "seq"}, sort_keys=True, ensure_ascii=False)
                if content in _emitted_set:
                    sys.stderr.write(f"DEDUP: {content[:100]}\n")
                    sys.stderr.flush()
                    return
                _emitted_set.add(content)
                _emitted_order.append(content)
                if len(_emitted_order) > _MAX_DEDUP:
                    _emitted_set.discard(_emitted_order.pop(0))
                sys.stderr.write(f"EMIT:   {content[:100]}\n")
                sys.stderr.flush()
                emit({"event": "step", "step": {k: v for k, v in step.items() if k != "seq"}})

            _last_error = [None, 0]
            def _suppress_dup_error(msg):
                now = time.time()
                if msg == _last_error[0] and now - _last_error[1] < 2:
                    return True
                _last_error[0] = msg
                _last_error[1] = now
                return False

            def _setup_page(p):
                p.on("console", handle_console)
                p.on("pageerror", lambda err, page=p: (
                    emit({"event": "error", "message": f"JS 错误(#{page.url}): {err}"})
                    if not _suppress_dup_error(str(err)) else None
                ))
                _all_pages.append(p)

            def handle_console(msg):
                if msg.text.startswith("__DSEP__"):
                    try:
                        step = json.loads(msg.text[len("__DSEP__"):])
                        sys.stderr.write(f"CONSOLE: {json.dumps(step)[:120]}\n")
                        sys.stderr.flush()
                        _emit_step(step)
                    except json.JSONDecodeError as e:
                        sys.stderr.write(f"JSON_ERR: {e}\n")
                        sys.stderr.flush()

            def on_new_page(new_page):
                sys.stderr.write(f"NEW_PAGE: {new_page.url}\n")
                sys.stderr.flush()
                _setup_page(new_page)

            context.on("page", on_new_page)

            page = context.new_page()
            _setup_page(page)

            def flush_all_queues():
                for p in list(_all_pages):
                    try:
                        result = p.evaluate("""
                            () => {
                                const q = window.__dsep_queue || [];
                                window.__dsep_queue = [];
                                return q;
                            }
                        """)
                        if result:
                            for step in result:
                                sys.stderr.write(f"QUEUE: {json.dumps(step)[:120]}\n")
                                sys.stderr.flush()
                                _emit_step(step)
                    except Exception:
                        pass

            if target_url and not target_url.startswith(("http://", "https://")):
                target_url = "https://" + target_url
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                emit({
                    "event": "step",
                    "step": {"action": "goto", "params": {"url": target_url}}
                })
            except Exception as e:
                emit({
                    "event": "error",
                    "message": f"页面导航失败: {target_url}\n{str(e)}"
                })
                sys.exit(1)

            while not stop_event.is_set():
                stop_event.wait(timeout=0.1)
                flush_all_queues()

            time.sleep(0.5)

            try:
                browser.close()
            except Exception:
                pass
    except Exception as e:
        emit({
            "event": "error",
            "message": f"{e}\n{traceback.format_exc()}"
        })
        sys.exit(1)
    finally:
        emit({"event": "done"})


if __name__ == "__main__":
    main()
