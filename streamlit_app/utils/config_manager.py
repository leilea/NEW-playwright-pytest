import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE = os.path.join(BASE_DIR, ".env")


def load_env():
    if not os.path.exists(ENV_FILE):
        return {"ENV": "qa"}
    content = {}
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                content[k.strip()] = v.strip()
    return content


def save_env(env_vars):
    os.makedirs(os.path.dirname(ENV_FILE), exist_ok=True)
    existing = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    existing[k.strip()] = v.strip()
    existing.update(env_vars)
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")
    for k, v in env_vars.items():
        os.environ[k] = v


def get_current_user() -> str:
    """返回当前登录用户名。优先读 `USER` / `USERNAME` 环境变量，兜底 "admin"。"""
    return os.environ.get("USER") or os.environ.get("USERNAME") or "admin"
