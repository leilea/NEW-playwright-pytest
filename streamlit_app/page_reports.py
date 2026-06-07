import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import glob
import streamlit as st

st.title("报告查看")

tab_allure, tab_html, tab_screenshots, tab_logs = st.tabs(
    ["Allure 报告", "HTML 报告", "截图", "日志"]
)

with tab_allure:
    index_path = os.path.join(Path(__file__).resolve().parent.parent, "allure-report", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            st.components.v1.html(f.read(), height=800, scrolling=True)
    else:
        st.info("Allure 报告尚未生成，请先运行测试。")
        st.code("allure generate allure-results -o allure-report --clean")

with tab_html:
    html_files = glob.glob(os.path.join(Path(__file__).resolve().parent.parent, "reports", "*.html"))
    if html_files:
        latest = max(html_files, key=os.path.getmtime)
        with open(latest, "r", encoding="utf-8") as f:
            st.components.v1.html(f.read(), height=800, scrolling=True)
        st.caption(f"文件: {os.path.basename(latest)}")
    else:
        st.info("未找到 HTML 报告。")

with tab_screenshots:
    screenshots_dir = os.path.join(Path(__file__).resolve().parent.parent, "screenshots")
    screenshots = sorted(glob.glob(os.path.join(screenshots_dir, "*.png")), key=os.path.getmtime, reverse=True)
    if screenshots:
        cols = st.columns(3)
        for i, shot in enumerate(screenshots):
            with cols[i % 3]:
                st.image(shot, caption=os.path.basename(shot), width='stretch')
    else:
        st.info("暂无截图。")

with tab_logs:
    logs_dir = os.path.join(Path(__file__).resolve().parent.parent, "logs")
    log_files = sorted(glob.glob(os.path.join(logs_dir, "*.log")), key=os.path.getmtime, reverse=True)
    if log_files:
        selected_log = st.selectbox("选择日志文件", log_files, format_func=lambda x: os.path.basename(x), key="reports_log")
        with open(selected_log, "r", encoding="utf-8") as f:
            st.text_area("日志内容", f.read(), height=600)
    else:
        st.info("暂无日志文件。")
