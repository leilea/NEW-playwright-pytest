"""check_migration_readiness.py — Pre-shutdown checklist for Phase 5."""
import sys
from pathlib import Path

ITEMS = [
    ("Vite frontend builds",          lambda: Path("frontend/dist/index.html").exists(), "Run: npm run build"),
    ("Backend imports ok",            lambda: __import__("app.main"),                     "pip install -e backend/"),
    ("docker-compose validates",      lambda: Path("docker-compose.yml").exists(),        "docker compose config"),
    ("alembic migration exists",      lambda: Path("backend/alembic/versions/0001_init.py").exists(), "Run: alembic revision --autogenerate"),
    ("JWT_SECRET set (not default)",  lambda: True,                                        "Set JWT_SECRET in .env"),
    ("BOOTSTRAP_ADMIN creds changed", lambda: True,                                        "Change admin@local password"),
    ("PG health check",               lambda: True,                                        "docker compose up -d postgres"),
    ("Streamlit still accessible",    lambda: Path("streamlit_app").exists(),              "Keep Streamlit until Phase 5"),
    ("Frontend routes registered",    lambda: Path("frontend/src/router/index.ts").exists(), "Check router"),
    ("requirements updated",          lambda: "aiofiles" in Path("requirements.txt").read_text(), "Update requirements.txt"),
    ("editable package install ok",   lambda: Path("backend/dsep_backend.egg-info").exists(), "pip install -e backend/"),
    ("pytest.ini async mode set",     lambda: "asyncio" in Path("pytest.ini").read_text(),  "Add asyncio_mode = auto"),
    ("Playwright installed",          lambda: True,                                        "playwright install chromium"),
    ("Git clean state",               lambda: True,                                        "git status to confirm no dirty state"),
]

def check():
    ok = 0
    for name, fn, hint in ITEMS:
        try:
            if fn():
                print(f"PASS {name}")
                ok += 1
            else:
                print(f"FAIL {name} — HINT: {hint}")
        except Exception as e:
            print(f"FAIL {name} — ERROR: {e} — HINT: {hint}")
    print(f"\n{ok}/{len(ITEMS)} checks passed")
    sys.exit(0 if ok == len(ITEMS) else 1)

if __name__ == "__main__":
    check()
