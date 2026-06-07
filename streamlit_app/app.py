import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

st.set_page_config(
    page_title="Playwright 测试仪表盘",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

from streamlit_app.utils.style import inject_design_system
inject_design_system()

dashboard = st.Page("page_dashboard.py", title="仪表盘", icon="📊")
runner = st.Page("page_runner.py", title="测试运行", icon="▶️")
testcases = st.Page("page_testcases.py", title="测试用例", icon="🧪", default=True)
reports = st.Page("page_reports.py", title="报告查看", icon="📁")
config = st.Page("page_config.py", title="系统配置", icon="⚙️")

pg = st.navigation([dashboard, runner, testcases, reports, config])

st.sidebar.image("https://playwright.dev/img/playwright-logo.svg", width=40)
st.sidebar.title("测试平台")
st.sidebar.caption("Playwright + pytest + Streamlit")
st.sidebar.divider()
st.sidebar.info(
    "**项目**: NEW-playwright-pytest\n"
    "**框架**: Playwright + pytest\n"
    "**技术栈**: Streamlit + Allure + Docker"
)

pg.run()
