"""canary_30d.py — Daily health probe during 30-day observation period."""
import sys
import httpx

CHECKS = [
    ("GET /api/health",          "/api/health",          200, None),
    ("GET /api/dashboard/summary","/api/dashboard/summary", 200, None),
    ("GET /api/suites",          "/api/suites",          200, None),
    ("GET /api/cases",           "/api/cases",           200, None),
]


def probe(base: str = "http://localhost:8000"):
    failures = 0
    for name, path, expect_code, _ in CHECKS:
        try:
            r = httpx.get(f"{base}{path}", timeout=10)
            if r.status_code != expect_code:
                print(f"FAIL {name}: status={r.status_code}")
                failures += 1
            else:
                print(f"OK   {name}")
        except Exception as e:
            print(f"FAIL {name}: {e}")
            failures += 1
    print(f"\n{failures}/{len(CHECKS)} failed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    probe(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000")
