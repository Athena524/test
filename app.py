"""
app.py — A股财务数据 Dashboard 主入口
运行：streamlit run app.py
"""

import streamlit as st
import pandas as pd

from data_loader import load_data, load_data_from_bytes
from metrics    import add_growth_metrics, compute_industry_summary
from charts     import (
    plot_market_trend, plot_industry_trend, plot_market_distribution,
    plot_stock_trend,  plot_stock_growth,
    plot_industry_rank_bar, plot_industry_companies_trend,
)
from utils import (
    METRIC_LABELS, sort_quarters,
    format_number, format_pct, get_prev_year_quarter,
)

# ================================================================
# 0. 页面基础配置
# ================================================================
st.set_page_config(
    page_title="A股财务数据 Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container{padding-top:3rem;padding-bottom:1rem}
[data-testid="stMetric"]{
    background:linear-gradient(135deg,#f0f4ff 0%,#e8eeff 100%);
    padding:.8rem 1rem;border-radius:.6rem;
    border-left:4px solid #3B82F6;
    box-shadow:0 1px 3px rgba(0,0,0,.08);
}
h1{text-align:center;color:#1e3a5f;border-bottom:3px solid #3B82F6;margin-top:1.5rem;padding-bottom:.8rem;margin-bottom:1.5rem}
</style>""", unsafe_allow_html=True)

# ================================================================
# 1. 侧边栏 — 数据源 & 全局控制
# ================================================================
with st.sidebar:
    st.header("🎛️ 控制面板")

    # ── 数据源 ──
    st.subheader("📂 数据源")
    uploaded = st.file_uploader(
        "上传 CSV（可选，留空使用示例数据）", type=["csv"]
    )
    if uploaded is not None:
        df_raw = load_data_from_bytes(uploaded.getvalue())
        st.success("✅ 已加载上传文件")
    else:
        df_raw = load_data()

    # 计算同比 / 环比
    df_all = add_growth_metrics(df_raw)

    st.divider()

    # ── 指标 ──
    st.subheader("📏 核心指标")
    metric = st.radio(
        "metric", list(METRIC_LABELS.keys()),
        format_func=lambda k: METRIC_LABELS[k],
        horizontal=True, label_visibility="collapsed",
    )
    metric_label = METRIC_LABELS[metric]

    st.divider()

    # ── 行业 ──
    all_industries = sorted(df_all["industry"].unique())
    st.subheader("🏭 行业筛选")
    sel_industries = st.multiselect(
        "ind", all_industries, default=all_industries,
        label_visibility="collapsed",
    )

    st.divider()

    # ── 季度范围 ──
    all_q = sort_quarters(df_all["year_quarter"].unique())
    st.subheader("📅 季度范围")
    if len(all_q) >= 2:
        q_lo, q_hi = st.select_slider(
            "qr", all_q, value=(all_q[0], all_q[-1]),
            label_visibility="collapsed",
        )
        sel_q = [q for q in all_q if q_lo <= q <= q_hi]
    else:
        sel_q = list(all_q)

# ================================================================
# 2. 应用筛选
# ================================================================
mask = df_all["industry"].isin(sel_industries) & df_all["year_quarter"].isin(sel_q)
df   = df_all[mask].copy()

valid_q = sort_quarters(df["year_quarter"].unique())
latest_q = valid_q[-1] if valid_q else ""

# 下载按钮
with st.sidebar:
    st.divider()
    st.subheader("📥 数据下载")
    st.download_button(
        "⬇ 下载筛选后数据 CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="a_share_filtered.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.caption(f"当前共 {len(df):,} 条记录")

# ================================================================
# 主标题
# ================================================================
st.markdown("# 📊 A股财务数据 Dashboard")

if df.empty:
    st.warning("⚠️ 当前筛选条件下无数据，请调整侧边栏筛选项。")
    st.stop()

# ================================================================
# SECTION 1  总体概表
# ================================================================
st.markdown("---")
st.subheader("📋 总体概表")

latest_df = df[df["year_quarter"] == latest_q]

# 去年同季
prev_yq  = get_prev_year_quarter(latest_q)
prev_df  = df[df["year_quarter"] == prev_yq] if prev_yq in valid_q else pd.DataFrame()

total_now = latest_df[metric].sum()
total_pre = prev_df[metric].sum() if not prev_df.empty else None
n_comp    = latest_df["ts_code"].nunique()
n_ind     = latest_df["industry"].nunique()
med_now   = latest_df[metric].median()

c1, c2, c3, c4 = st.columns(4)
with c1:
    delta = None
    if total_pre and abs(total_pre) > 0:
        delta = f"{(total_now - total_pre) / abs(total_pre) * 100:+.1f}% 同比"
    st.metric(f"市场{metric_label}合计（{latest_q}）",
              format_number(total_now), delta=delta)
with c2:
    st.metric("覆盖公司数", f"{n_comp} 家")
with c3:
    st.metric("覆盖行业数", f"{n_ind} 个")
with c4:
    st.metric(f"{metric_label}中位数", format_number(med_now))

# 行业汇总表
st.markdown(f"**📊 行业汇总 — {latest_q}**")
ind_sum = compute_industry_summary(df, metric, latest_q)
disp = ind_sum.copy()
for c in ["合计", "均值", "中位数"]:
    if c in disp.columns:
        disp[c] = disp[c].apply(format_number)
st.dataframe(disp, use_container_width=True, hide_index=True)

# ================================================================
# SECTION 2  趋势与历史时序
# ================================================================
st.markdown("---")
st.subheader("📈 趋势与历史时序")

left, right = st.columns(2)
with left:
    st.plotly_chart(
        plot_market_trend(df, metric, metric_label, valid_q),
        use_container_width=True, key="c_mkt",
    )
with right:
    st.plotly_chart(
        plot_industry_trend(df, metric, metric_label, valid_q),
        use_container_width=True, key="c_ind",
    )

st.plotly_chart(
    plot_market_distribution(df, metric, metric_label, valid_q),
    use_container_width=True, key="c_box",
)

# ================================================================
# SECTION 3  个股对比
# ================================================================
st.markdown("---")
st.subheader("🔍 个股对比")

stocks = df[["ts_code", "name"]].drop_duplicates().sort_values("ts_code")
stock_map = {
    f"{r['name']}（{r['ts_code']}）": r["ts_code"]
    for _, r in stocks.iterrows()
}

fc1, fc2 = st.columns([4, 1])
with fc1:
    defaults = list(stock_map.keys())[:3]
    sel_labels = st.multiselect(
        "🔎 个股筛选", list(stock_map.keys()),
        default=defaults, placeholder="输入公司名或代码搜索…",
    )
with fc2:
    gtype = st.selectbox("增速类型", ["同比 (YoY)", "环比 (QoQ)"])

sel_codes = [stock_map[lb] for lb in sel_labels]

if sel_codes:
    df_stk = df[df["ts_code"].isin(sel_codes)]

    s1, s2 = st.columns(2)
    with s1:
        st.plotly_chart(
            plot_stock_trend(df_stk, metric, metric_label, valid_q),
            use_container_width=True, key="c_stk",
        )
    with s2:
        sfx   = "_yoy" if "YoY" in gtype else "_qoq"
        gcol  = f"{metric}{sfx}"
        glab  = "同比增速" if "YoY" in gtype else "环比增速"
        st.plotly_chart(
            plot_stock_growth(df_stk, gcol, glab, valid_q),
            use_container_width=True, key="c_grw",
        )

    # 明细
    with st.expander("📋 查看个股明细数据", expanded=False):
        want = ["year_quarter", "ts_code", "name", "industry",
                "revenue", "net_profit", "capex",
                f"{metric}_yoy", f"{metric}_qoq"]
        have = [c for c in want if c in df_stk.columns]
        det  = df_stk[have].sort_values(["name", "year_quarter"]).reset_index(drop=True)
        fmt  = det.copy()
        for c in ["revenue", "net_profit", "capex"]:
            if c in fmt:
                fmt[c] = fmt[c].apply(lambda v: format_number(v) if pd.notna(v) else "N/A")
        for c in [f"{metric}_yoy", f"{metric}_qoq"]:
            if c in fmt:
                fmt[c] = fmt[c].apply(lambda v: format_pct(v) if pd.notna(v) else "N/A")
        st.dataframe(fmt, use_container_width=True, hide_index=True)
else:
    st.info("👆 请在上方选择至少一只股票进行对比分析。")

# ================================================================
# SECTION 4  行业下钻
# ================================================================
st.markdown("---")
st.subheader("🏭 行业下钻分析")

avail_ind = sorted(df["industry"].unique())
drill_ind = st.selectbox("选择行业，查看内部公司明细", avail_ind)

if drill_ind:
    d1, d2 = st.columns(2)
    with d1:
        st.plotly_chart(
            plot_industry_rank_bar(df, metric, metric_label, drill_ind, latest_q),
            use_container_width=True, key="c_dr1",
        )
    with d2:
        st.plotly_chart(
            plot_industry_companies_trend(df, metric, metric_label, drill_ind, valid_q),
            use_container_width=True, key="c_dr2",
        )

# ================================================================
# 页脚
# ================================================================
st.markdown("---")
st.caption(
    "📊 A股财务数据 Dashboard · 数据仅供学习研究，不构成投资建议 · "
    "Powered by Streamlit + Plotly"
)