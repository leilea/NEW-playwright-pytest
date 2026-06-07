"""通用 TTL 缓存装饰器。

替代 streamlit 的 @st.cache_data(ttl=N)，让 utils 层不依赖任何 UI 框架。
"""
import functools
import time
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def ttl_cache(ttl_seconds: int) -> Callable[[F], F]:
    """带 TTL 的内存缓存装饰器。

    行为：
    - 第一次调用执行函数并缓存 (timestamp, value)
    - ttl_seconds 内重复调用（相同参数）直接返回缓存
    - ttl 过期后重新执行

    单进程 / 单线程假设；并发场景请用 threading.Lock 包裹或换 cachetools.TTLCache。
    """
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")

    def decorator(fn: F) -> F:
        cache: dict = {}

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            cached = cache.get(key)
            if cached is not None:
                ts, value = cached
                if now - ts < ttl_seconds:
                    return value
            value = fn(*args, **kwargs)
            cache[key] = (now, value)
            return value

        wrapper.cache_clear = cache.clear  # type: ignore[attr-defined]
        wrapper.cache = cache  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator
