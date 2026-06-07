import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from streamlit_app.utils.test_executor import run_pytest
from streamlit_app.utils.allure_reader import get_summary
from streamlit_app.utils.report_cache import save_run

st.title("测试运行")

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        env = st.selectbox("环境", ["qa", "dev"], index=0, key="runner_env")
        markers = st.selectbox("测试类型", ["all", "smoke", "api"], index=0, key="runner_markers")
    with col2:
        browser = st.selectbox("浏览器", ["chromium", "firefox", "webkit", "edge"], index=0, key="runner_browser")
        extra_args = st.text_input("额外 pytest 参数（可选）", placeholder="-k test_login", key="runner_args")

if st.button("运行测试", type="primary", width='stretch', key="runner_go"):
    pytest_markers = None if markers == "all" else markers
    extra = extra_args.strip().split() if extra_args.strip() else None

    output_area = st.empty()
    full_output = []
    with st.spinner("正在运行 pytest..."):
        for line in run_pytest(env=env, browser=browser, markers=pytest_markers, extra_args=extra):
            full_output.append(line)
            display = "".join(full_output[-50:])
            output_area.code(display, language="")

    st.success("测试完成！")
    summary = get_summary()
    save_run(summary, env, browser, markers)

    st.subheader("运行摘要")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总数", summary["total"])
    c2.metric("通过", summary["passed"])
    c3.metric("失败", summary["failed"])
    c4.metric("通过率", f"{summary['pass_rate']}%")

    with st.expander("完整输出", expanded=False):
        st.code("".join(full_output), language="")
