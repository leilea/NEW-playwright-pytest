# global_setup.py
import shutil
from pathlib import Path

def main():
    for d in ["allure-results", "allure-report", "test-results"]:
        p = Path(d)
        if p.exists():
            shutil.rmtree(p)
    for d in ["logs", "reports", "screenshots"]:
        Path(d).mkdir(exist_ok=True)
    print("Global setup done.")

if __name__ == "__main__":
    main()