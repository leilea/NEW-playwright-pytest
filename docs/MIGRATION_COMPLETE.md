# Migration Complete — Phase 5 Archive

> **Date:** 2026-06-08  
> **Status:** Phase 5 complete, Streamlit retired

## What was removed
- `streamlit_app/` — the full Streamlit monolith (5 pages, controllers, services, utils)
- `.streamlit/config.toml` — Streamlit configuration
- Streamlit deps from `requirements.txt`

## What replaced it
| Old (Streamlit)      | New (Vue 3 + FastAPI)           |
|----------------------|---------------------------------|
| page_dashboard.py    | Dashboard.vue + /api/dashboard  |
| page_testrun.py      | Runs.vue + /api/runs + WS       |
| page_testcases.py    | CaseEditor.vue + StepEditor + Recorder |
| page_reports.py      | Reports.vue + /api/reports      |
| page_config.py       | Config.vue + /api/config         |

## Verification
```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend
cd frontend && npm run dev

# Full test suite
pytest backend/tests/ -v
cd frontend && npx vitest run

# Canary probe (30-day observation)
python backend/scripts/canary_30d.py

# Readiness checklist
python backend/scripts/check_migration_readiness.py
```

## Post-migration cleanup
1. Remove `streamlit_app/` directory
2. Remove `.streamlit/` directory
3. Clean `requirements.txt` (remove streamlit, plotly, pandas if only used by Streamlit)
4. Archive `Dockerfile.txt` → replaced by `docker-compose.yml` + `backend/Dockerfile`
5. Delete legacy JSON stores in `logs/` (suites.json, testcases.json — now in PostgreSQL)
