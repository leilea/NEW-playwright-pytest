# backend/tests/integration/test_docker_compose.py
import subprocess, shutil
import pytest
from pathlib import Path

@pytest.mark.skipif(not shutil.which("docker"), reason="docker not available")
def test_docker_compose_validates():
    """docker-compose config must pass schema validation"""
    result = subprocess.run(
        ["docker", "compose", "config", "--quiet"],
        cwd=Path(__file__).parents[3],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"compose invalid: {result.stderr}"
