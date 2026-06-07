# config/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(log_dir="logs", level=logging.INFO):
    Path(log_dir).mkdir(exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(level)

    fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    file_handler = logging.FileHandler(f"{log_dir}/test.log")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # 控制第三方库日志级别
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)