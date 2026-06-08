from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from app.config import settings

router = APIRouter(tags=["reports"])

LOG_DIR = Path(settings.log_dir)
ALLURE_DIR = Path(settings.allure_results_dir)
REPORT_DIR = LOG_DIR.parent / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/reports/runs")
async def list_run_reports():
    runs = []
    if LOG_DIR.exists():
        for p in sorted(LOG_DIR.rglob("*.log"), reverse=True)[:50]:
            runs.append({
                "name": p.name,
                "path": str(p.relative_to(LOG_DIR.parent)),
                "size": p.stat().st_size,
                "modified": p.stat().st_mtime,
            })
    if REPORT_DIR.exists():
        for p in sorted(REPORT_DIR.rglob("*.html"), reverse=True)[:50]:
            runs.append({
                "name": p.name,
                "path": str(p.relative_to(LOG_DIR.parent)),
                "size": p.stat().st_size,
                "modified": p.stat().st_mtime,
            })
    return runs


@router.get("/reports/files")
async def list_report_files():
    files = []
    report_dirs = [ALLURE_DIR, REPORT_DIR, LOG_DIR]
    for d in report_dirs:
        if d.exists():
            for p in d.iterdir():
                if p.is_file():
                    files.append({
                        "name": p.name,
                        "path": str(p.relative_to(LOG_DIR.parent)),
                        "size": p.stat().st_size,
                    })
    return files


@router.get("/reports/raw/{subpath:path}")
async def serve_report_file(subpath: str):
    base = LOG_DIR.parent
    full = (base / subpath).resolve()
    if not str(full).startswith(str(base.resolve())):
        return JSONResponse({"error": "path traversal"}, status_code=403)
    if not full.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(full)
