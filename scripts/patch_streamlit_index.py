"""
streamlit index.html <base> 补丁脚本 (幂等)

目的: 修复 streamlit SPA 在直接页面 URL (如 /page_testcases) 下的相对 URL 解析问题。
通过在 <head> 顶部注入 <base href="/"> 强制所有相对 URL 解析到根路径。

适用场景: streamlit 升级 (pip install -U streamlit) 后会自动覆盖 index.html,
需要重新打补丁。也可用于首次部署或回滚。

用法:
  python scripts/patch_streamlit_index.py           # 应用补丁 (幂等)
  python scripts/patch_streamlit_index.py --revert  # 还原到原始状态
  python scripts/patch_streamlit_index.py --check   # 仅检查当前状态, 退出码 0=已应用, 1=未应用

副作用:
  - 应用补丁时: 备份原文件为 <index.html.original>, 原地修改 index.html
  - 还原时: 从 .original 恢复 (若存在), 否则要求手动恢复
  - streamlit 必须重启才能生效 (静态文件被服务器进程加载到内存)
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

DEFAULT_INDEX = Path(r"C:\Users\ASUS\AppData\Local\Programs\Python\Python313\Lib\site-packages\streamlit\static\index.html")
DEFAULT_BACKUP = DEFAULT_INDEX.with_suffix(".html.original")

BASE_TAG = '<base href="/" />'
HEAD_OPEN = "  <head>"
META_CHARSET = '<meta charset="UTF-8" />'

BASE_PATTERN = re.compile(r'<base\s+href\s*=\s*["\047]/["\047]\s*/?>', re.IGNORECASE)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def is_patched(content: str) -> bool:
    return bool(BASE_PATTERN.search(content))


def apply(path: Path, backup: Path) -> None:
    if not path.exists():
        print(f"ERR: index.html 不存在: {path}", file=sys.stderr)
        sys.exit(1)

    content = _read(path)

    if is_patched(content):
        print(f"[SKIP] 已存在 <base> 标签, 无需重复打补丁: {path}")
        return

    if not backup.exists():
        shutil.copy2(path, backup)
        print(f"[BACKUP] 原文件已备份: {backup}")

    if HEAD_OPEN not in content:
        print(f"ERR: 未找到锚点 '{HEAD_OPEN}', 无法安全插入。", file=sys.stderr)
        print(f"     请手动检查 {path} 的 <head> 结构。", file=sys.stderr)
        sys.exit(1)

    if META_CHARSET not in content:
        print(f"WARN: 未找到 '{META_CHARSET}', 改用 HEAD 锚点之后插入。", file=sys.stderr)
        new_content = content.replace(HEAD_OPEN, f"{HEAD_OPEN}\n    {BASE_TAG}", 1)
    else:
        new_content = content.replace(META_CHARSET, f"{BASE_TAG}\n    {META_CHARSET}", 1)

    _write(path, new_content)
    print(f"[PATCHED] 已插入 {BASE_TAG}: {path}")
    print(f"[NEXT] 请重启 streamlit 服务以使补丁生效。")


def revert(path: Path, backup: Path) -> None:
    if not backup.exists():
        print(f"ERR: 备份文件不存在: {backup}", file=sys.stderr)
        print(f"     无法自动还原, 请手动恢复 {path}。", file=sys.stderr)
        sys.exit(1)

    shutil.copy2(backup, path)
    print(f"[REVERTED] 已从备份还原: {backup} -> {path}")
    print(f"[NEXT] 请重启 streamlit 服务以使还原生效。")


def check(path: Path) -> int:
    if not path.exists():
        print(f"ERR: index.html 不存在: {path}", file=sys.stderr)
        return 1
    if is_patched(_read(path)):
        print(f"[PATCHED] {path}")
        return 0
    print(f"[NOT PATCHED] {path}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="streamlit index.html <base> 补丁脚本")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX, help="目标 index.html 路径")
    parser.add_argument("--backup", type=Path, default=DEFAULT_BACKUP, help="备份文件路径")
    parser.add_argument("--revert", action="store_true", help="还原补丁")
    parser.add_argument("--check", action="store_true", help="仅检查状态")
    args = parser.parse_args()

    if args.revert:
        revert(args.index, args.backup)
        return 0
    if args.check:
        return check(args.index)
    apply(args.index, args.backup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
