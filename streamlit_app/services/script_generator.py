"""步骤 → 脚本 生成器。纯函数，零外部依赖，可单测。

未来 API 对应：POST /api/testcases/:id/regenerate-script
"""
from typing import List, Dict


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def generate_script(steps: List[Dict], target_url: str = "") -> str:
    lines = [
        "import re",
        "from playwright.sync_api import Playwright, sync_playwright, expect",
        "",
        "",
        "def run(playwright: Playwright) -> None:",
        "    browser = playwright.chromium.launch(headless=False)",
        "    context = browser.new_context()",
        "    page = context.new_page()",
    ]
    for step in steps:
        action = step.get("action", "")
        selector = _escape(step.get("selector", "").strip())
        value = _escape(step.get("value", "").strip())
        if action == "navigate":
            url = value or selector
            if url:
                lines.append(f'    page.goto("{url}")')
        elif action == "click":
            lines.append(f'    page.{selector}.click()')
        elif action == "dblclick":
            lines.append(f'    page.{selector}.dblclick()')
        elif action == "fill":
            lines.append(f'    page.{selector}.fill("{value}")')
        elif action == "hover":
            lines.append(f'    page.{selector}.hover()')
        elif action == "clear":
            lines.append(f'    page.{selector}.clear()')
        elif action == "scroll":
            lines.append(f'    page.{selector}.scroll_into_view_if_needed()')
        elif action == "select":
            lines.append(f'    page.{selector}.select_option("{value}")')
        elif action == "check":
            lines.append(f'    page.{selector}.check()')
        elif action == "uncheck":
            lines.append(f'    page.{selector}.uncheck()')
        elif action == "verify":
            lines.append(f'    expect(page.{selector}).to_be_visible()')
    lines.extend([
        "",
        "    # ---------------------",
        "    context.close()",
        "    browser.close()",
        "",
        "",
        "with sync_playwright() as playwright:",
        "    run(playwright)",
        "",
    ])
    return "\n".join(lines)
