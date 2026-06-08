import subprocess, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # backend/

def test_alembic_env_present():
    assert (ROOT / "alembic/env.py").exists()
    assert (ROOT / "alembic/versions/0001_init.py").exists()

def test_alembic_init_creates_four_schemas():
    txt = (ROOT / "alembic/versions/0001_init.py").read_text(encoding="utf-8")
    for schema in ("auth", "catalog", "runtime", "audit"):
        assert f'CREATE SCHEMA IF NOT EXISTS {schema}' in txt
