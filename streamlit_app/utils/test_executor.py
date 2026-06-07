import subprocess
import os
import tempfile
import threading
import queue

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_pytest(env="qa", browser="chromium", markers=None, extra_args=None):
    cmd = ["pytest", "-v"]
    cmd.extend(["--browser", browser])
    cmd.extend(["--alluredir", os.path.join(BASE_DIR, "allure-results")])
    cmd.extend(["--html", os.path.join(BASE_DIR, "reports", "report.html")])
    cmd.append("--self-contained-html")

    if markers:
        cmd.extend(["-m", markers])
    if extra_args:
        cmd.extend(extra_args)

    env_dict = {**os.environ, "ENV": env, "PYTHONPATH": BASE_DIR}
    log_file = os.path.join(BASE_DIR, "logs", "test_streamlit.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env_dict,
        cwd=BASE_DIR,
        bufsize=1,
    )

    output_queue = queue.Queue()
    completed = threading.Event()

    def _reader():
        try:
            for line in iter(proc.stdout.readline, ""):
                output_queue.put(line)
        finally:
            proc.stdout.close()
            completed.set()

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()

    output_lines = []
    with open(log_file, "w", encoding="utf-8") as lf:
        while True:
            try:
                line = output_queue.get(timeout=0.1)
                output_lines.append(line)
                lf.write(line)
                lf.flush()
                yield line
            except queue.Empty:
                if completed.is_set() and output_queue.empty():
                    break

    proc.wait()
    exit_code = proc.returncode

    _generate_allure_report()
    yield f"\n[STREAMLIT] pytest exit code: {exit_code}"
    yield f"[STREAMLIT] Log saved to: {log_file}"


def _generate_allure_report():
    try:
        subprocess.run(
            ["allure", "generate", os.path.join(BASE_DIR, "allure-results"),
             "-o", os.path.join(BASE_DIR, "allure-report"), "--clean"],
            capture_output=True, text=True, cwd=BASE_DIR,
        )
    except FileNotFoundError:
        pass
