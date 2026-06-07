import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from streamlit_app.utils.config_manager import load_env, save_env

st.title("系统配置")

env_vars = load_env()

st.subheader("录制默认网址")
st.caption("录制开始时浏览器打开的目标地址")
new_recording_url = st.text_input(
    "录制默认网址",
    value=env_vars.get("RECORDING_URL", ""),
    placeholder="留空则使用 test_config.py 中的环境配置",
    key="cfg_recording_url",
)
if st.button("保存录制配置", type="primary", key="cfg_save_recording"):
    save_env({"RECORDING_URL": new_recording_url})
    st.success("录制默认网址已保存！")

st.divider()
st.subheader("环境变量")
st.caption("文件: .env")

new_env = st.text_input("ENV", value=env_vars.get("ENV", "qa"), key="cfg_env")
new_extra = st.text_input("SECRET_KEY（可选）", value=env_vars.get("SECRET_KEY", ""), type="password", key="cfg_secret")

if st.button("保存 .env", type="primary", key="cfg_save"):
    updates = {"ENV": new_env}
    if new_extra:
        updates["SECRET_KEY"] = new_extra
    save_env(updates)
    st.success("配置已保存！部分修改需要重启应用。")

st.divider()
st.subheader("环境配置覆盖")
st.caption("留空则使用默认值")

with st.expander("QA 环境", expanded=False):
    qa_base = st.text_input("QA Base URL", value=env_vars.get("QA_BASE_URL", ""), placeholder="https://demoqa.com", key="cfg_qa_base")
    qa_api = st.text_input("QA API Base URL", value=env_vars.get("QA_API_BASE_URL", ""), placeholder="https://demoqa.com", key="cfg_qa_api")

with st.expander("DEV 环境", expanded=False):
    dev_base = st.text_input("DEV Base URL", value=env_vars.get("DEV_BASE_URL", ""), placeholder="https://dev.demoqa.com", key="cfg_dev_base")
    dev_api = st.text_input("DEV API Base URL", value=env_vars.get("DEV_API_BASE_URL", ""), placeholder="https://dev.demoqa.com", key="cfg_dev_api")

if st.button("保存环境配置", type="primary", key="cfg_save_env_urls"):
    updates = {}
    if qa_base: updates["QA_BASE_URL"] = qa_base
    if qa_api: updates["QA_API_BASE_URL"] = qa_api
    if dev_base: updates["DEV_BASE_URL"] = dev_base
    if dev_api: updates["DEV_API_BASE_URL"] = dev_api
    if updates:
        save_env(updates)
        st.success("环境配置已保存！")
        st.rerun()
    else:
        st.info("未输入任何值，无变更。")

st.divider()
st.subheader("当前生效配置")
try:
    from config.test_config import TestConfig
    cfg = TestConfig()
    for k, v in {
        "当前环境": cfg.environment,
        "基础 URL": cfg.base_url,
        "接口 URL": cfg.api_base_url,
        "忽略 HTTPS 错误": str(cfg.ignore_https_errors),
    }.items():
        st.text(f"{k}: {v}")
except Exception as e:
    st.caption(f"读取配置失败: {e}")
