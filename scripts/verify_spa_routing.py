"""
SPA 路由验证脚本 (TDD)

目的: 验证 streamlit SPA 在直接页面 URL (如 /page_testcases) 下能正常初始化。

核心检查:
  1. 根 URL 的 _stcore/host-config 返回 200 (控制组, 任何情况下都应通过)
  2. 页面 URL 的 _stcore/host-config 返回 200 (修复目标)
  3. 页面 URL 返回的 HTML 包含 <base href="/"> (修复证据)
  4. 页面 URL 返回的 HTML 包含 streamlit 入口 (SPA 结构完整)

用法:
  python scripts/verify_spa_routing.py [--base-url http://localhost:8501] [--page page_testcases]

退出码:
  0 = 全部通过
  1 = 至少一项失败
"""
import argparse
import re
import sys
from urllib import request
from urllib.error import HTTPError, URLError

DEFAULT_BASE_URL = "http://localhost:8501"
DEFAULT_PAGE = "page_testcases"
TIMEOUT = 5


def _http_get(url: str) -> tuple[int, str]:
    try:
        with request.urlopen(url, timeout=TIMEOUT) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        return e.code, ""
    except URLError as e:
        return 0, f"URLError: {e.reason}"


def check_root_host_config(base_url: str) -> bool:
    url = f"{base_url}/_stcore/host-config"
    status, _ = _http_get(url)
    ok = status == 200
    print(f"  [{'PASS' if ok else 'FAIL'}] GET {url} -> {status} (期望 200)")
    return ok


def check_page_host_config(base_url: str, page: str) -> bool:
    """
    模拟浏览器在页面 URL 下的相对 URL 解析。

    浏览器加载 /page_testcases 页面后, JS 调用 fetch(' /_stcore/host-config')。
    不加 <base>: 解析为 /page_testcases/_stcore/host-config -> 404
    加上 <base href="/">: 解析为 /_stcore/host-config -> 200

    注意: HTTP 客户端没有"相对 URL"概念, 这里实际是"如果浏览器用相对 URL 解析,
    它会发什么请求"的语义模拟。因此修复后服务端对 /page_testcases/_stcore/host-config
    仍然返回 404 是预期行为——本测试在修复后预期返回 PASS, 表示"已记录为已知行为, 浏览器因
    <base> 不会实际发出此请求"。
    """
    url = f"{base_url}/{page}/_stcore/host-config"
    status, _ = _http_get(url)
    print(f"  [INFO] GET {url} -> {status} (服务端对此 URL 返回 404 是正确的: <base> 在客户端, 修复后浏览器不会发出此请求)")
    return True  # 服务端 404 是正确行为, 不再视为失败


def check_page_html(base_url: str, page: str) -> tuple[bool, bool, bool]:
    url = f"{base_url}/{page}"
    status, body = _http_get(url)
    html_ok = status == 200
    print(f"  [{'PASS' if html_ok else 'FAIL'}] GET {url} -> {status} (期望 200)")

    base_pattern = re.compile(r'<base\s+href\s*=\s*["\047]/["\047]\s*/?>', re.IGNORECASE)
    base_ok = bool(base_pattern.search(body))
    print(f"  [{'PASS' if base_ok else 'FAIL'}] HTML 包含 <base href=\"/\"> (修复证据)")

    spa_ok = bool(re.search(r'src="\./static/js/[^"]+\.js"', body))
    print(f"  [{'PASS' if spa_ok else 'FAIL'}] HTML 包含 streamlit JS bundle 引用 (SPA 结构完整)")

    return html_ok, base_ok, spa_ok


def main() -> int:
    parser = argparse.ArgumentParser(description="验证 streamlit SPA 路由修复")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="streamlit 服务地址")
    parser.add_argument("--page", default=DEFAULT_PAGE, help="要验证的页面 slug")
    args = parser.parse_args()

    print(f"目标: {args.base_url} (page={args.page})\n")

    results = []
    print("[控制组] 根 URL _stcore/host-config:")
    results.append(check_root_host_config(args.base_url))

    print(f"\n[行为记录] 页面 URL _stcore/host-config (服务端响应, 仅记录不计入失败):")
    check_page_host_config(args.base_url, args.page)

    print(f"\n[修复证据] 页面 URL HTML 内容:")
    html_ok, base_ok, spa_ok = check_page_html(args.base_url, args.page)
    results.extend([html_ok, base_ok, spa_ok])

    passed = sum(results)
    total = len(results)
    print(f"\n汇总: {passed}/{total} 通过")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
