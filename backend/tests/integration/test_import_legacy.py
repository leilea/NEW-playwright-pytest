from pathlib import Path


def test_import_script_exists():
    assert Path("backend/scripts/import_legacy_json.py").exists()


def test_verify_script_exists():
    assert Path("backend/scripts/verify_legacy_migration.py").exists()
