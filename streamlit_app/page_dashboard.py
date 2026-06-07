import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_app.utils.allure_reader import get_summary, get_feature_stats, get_recent_results
from streamlit_app.utils.report_cache import load_trends

st.title("测试仪表盘")

summary = get_summary()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("总数", summary["total"])
col2.metric("通过", summary["passed"], delta_color="off")
col3.metric("失败", summary["failed"], delta_color="off")
col4.metric("跳过", summary["skipped"], delta_color="off")
col5.metric("通过率", f"{summary['pass_rate']}%")

col_pie, col_bar = st.columns(2)
with col_pie:
    fig = px.pie(
        names=["通过", "失败", "跳过", "损坏"],
        values=[summary["passed"], summary["failed"], summary["skipped"], summary["broken"]],
        title="测试结果分布",
        color_discrete_map={"Passed": "#00cc96", "Failed": "#ef553b", "Skipped": "#ffa15a", "Broken": "#ab63fa"},
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, width='stretch')

with col_bar:
    feature_df = get_feature_stats()
    if not feature_df.empty:
        fig2 = px.bar(feature_df, x="feature", y=["passed", "failed"],
                      title="按模块统计", barmode="group",
                      color_discrete_map={"passed": "#00cc96", "failed": "#ef553b"})
        fig2.update_layout(xaxis_title="", yaxis_title="Count")
        st.plotly_chart(fig2, width='stretch')

st.subheader("最近结果")
recent = get_recent_results()
if not recent.empty:
    def _color(val):
        if val == "passed":
            return "background-color: #d4edda"
        elif val == "failed":
            return "background-color: #f8d7da"
        return "background-color: #fff3cd"
    styled = recent.style.map(_color, subset=["status"])
    st.dataframe(styled, width='stretch', height=300)
else:
    st.info("暂无测试结果，请先运行测试！")

st.subheader("历史趋势")
trends = load_trends()
if trends:
    trend_df = pd.DataFrame(trends)
    trend_df["run_id"] = range(1, len(trend_df) + 1)
    fig3 = px.line(trend_df, x="run_id", y="pass_rate",
                   markers=True, title="通过率趋势")
    fig3.update_layout(xaxis_title="运行次数", yaxis_title="通过率 (%)", yaxis_range=[0, 100])
    st.plotly_chart(fig3, width='stretch')
else:
    st.info("暂无历史数据。")
