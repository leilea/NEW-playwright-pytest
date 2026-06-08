"""Optional: import legacy JSON data (suites + cases) into PostgreSQL."""
import asyncio, json
from pathlib import Path
from app.db.session import session_scope
from app.services.suite_service import create_suite
from app.services.case_service import create_case


async def import_all(suites_path: Path, cases_path: Path) -> tuple[int, int]:
    suites = json.loads(suites_path.read_text()) if suites_path.exists() else []
    cases = json.loads(cases_path.read_text()) if cases_path.exists() else []
    n_s, n_c = 0, 0
    async with session_scope() as db:
        for s in suites:
            await create_suite(db, name=s["name"], description=s.get("description", ""))
            n_s += 1
        for c in cases:
            await create_case(db, suite_id=c["suite_id"], name=c["name"],
                              tags=c.get("tags", []), steps=c.get("steps", []))
            n_c += 1
    return n_s, n_c


if __name__ == "__main__":
    s, c = asyncio.run(import_all(
        Path("logs/suites.json"), Path("logs/testcases.json"),
    ))
    print(f"imported suites={s} cases={c}")
