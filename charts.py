"""
charts.py — Plotly 图表函数模块
所有金额默认转为「亿元」显示，统一风格配色。
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ── 全局配色 & 基础布局 ──────────────────────────────
PALETTE = [
    "#2563EB", "#DC2626", "#F59E0B", "#10B981", "#8B5CF6",
    "#EC4899", "#06B6D4", "#84CC16", "#F97316", "#6366F1",
]

_BASE = dict(
    font=dict(family="SimHei, Microsoft YaHei, Arial, sans-serif", size=12),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(248,250,252,1)",
    hovermode="x unified",
    margin=dict(l=50, r=30, t=55, b=50),
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1, font=dict(size=11)),
)


def _style(fig, height=400, **kw):
    """统一应用图表样式"""
    fig.update_layout(**{**_BASE, "height": height, **kw})
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.06)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.08)")
    return fig


# ══════════════════════════════════════════════════════
# Section 2  全市场 & 行业趋势
# ══════════════════════════════════════════════════════

def plot_market_trend(df, metric, label, q_order):
    """全市场指标趋势 — 柱状 + 同比折线（双 Y 轴）"""
    agg = df.groupby("year_quarter")[metric].sum().reset_index(name="total")

    # 确保按季度顺序
    order = {q: i for i, q in enumerate(q_order)}
    agg["_s"] = agg["year_quarter"].map(order)
    agg = agg.dropna(subset=["_s"]).sort_values("_s").drop(columns="_s")

    agg["yi"]  = agg["total"] / 1e8
    agg["yoy"] = agg["total"].pct_change(periods=4) * 100   # 同比

    fig = go.Figure()

    # 柱状 — 绝对值
    fig.add_trace(go.Bar(
        x=agg["year_quarter"], y=agg["yi"],
        name=f"{label}（亿元）",
        marker_color="#3B82F6", opacity=0.75,
        hovertemplate="%{x}<br>%{y:,.1f} 亿<extra></extra>",
    ))

    # 折线 — 同比增速
    yoy = agg.dropna(subset=["yoy"])
    if len(yoy):
        fig.add_trace(go.Scatter(
            x=yoy["year_quarter"], y=yoy["yoy"],
            name="同比增速(%)", mode="lines+markers",
            line=dict(color="#EF4444", width=2.5),
            marker=dict(size=7), yaxis="y2",
            hovertemplate="%{x}<br>同比 %{y:+.1f}%<extra></extra>",
        ))

    fig.update_layout(
        title=dict(text=f"全市场 {label} 趋势", font=dict(size=15)),
        xaxis=dict(title="季度"),
        yaxis=dict(title=f"{label}（亿元）"),
        yaxis2=dict(title="同比(%)", overlaying="y", side="right", showgrid=False),
    )
    return _style(fig, 400)


def plot_industry_trend(df, metric, label, q_order):
    """行业对比趋势 — 多折线"""
    agg = df.groupby(["industry", "year_quarter"])[metric].sum().reset_index()
    agg["yi"] = agg[metric] / 1e8

    fig = px.line(
        agg, x="year_quarter", y="yi", color="industry", markers=True,
        title=f"行业 {label} 趋势对比（亿元）",
        labels={"year_quarter": "季度", "yi": f"{label}（亿元）", "industry": "行业"},
        category_orders={"year_quarter": q_order},
        color_discrete_sequence=PALETTE,
    )
    return _style(fig, 400)


def plot_market_distribution(df, metric, label, q_order):
    """市场分位数分布 — 箱线图（按行业着色）"""
    tmp = df.copy()
    tmp["yi"] = tmp[metric] / 1e8

    fig = px.box(
        tmp, x="year_quarter", y="yi", color="industry",
        title=f"全市场 {label} 分位数分布（亿元）",
        labels={"year_quarter": "季度", "yi": f"{label}（亿元）", "industry": "行业"},
        category_orders={"year_quarter": q_order},
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(quartilemethod="linear")
    return _style(fig, 430)


# ══════════════════════════════════════════════════════
# Section 3  个股对比
# ══════════════════════════════════════════════════════

def plot_stock_trend(df, metric, label, q_order):
    """个股趋势对比 — 折线"""
    tmp = df.copy()
    tmp["yi"] = tmp[metric] / 1e8

    fig = px.line(
        tmp, x="year_quarter", y="yi", color="name", markers=True,
        title=f"个股 {label} 趋势（亿元）",
        labels={"year_quarter": "季度", "yi": f"{label}（亿元）", "name": "公司"},
        category_orders={"year_quarter": q_order},
        color_discrete_sequence=PALETTE,
    )
    return _style(fig, 430)


def plot_stock_growth(df, col, label, q_order):
    """个股增速对比 — 分组柱状"""
    tmp = df.dropna(subset=[col])

    if tmp.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无增速数据（需更多季度）",
                           showarrow=False, font=dict(size=14, color="gray"),
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return _style(fig, 430, title=dict(text=f"个股 {label} 对比"))

    fig = px.bar(
        tmp, x="year_quarter", y=col, color="name", barmode="group",
        title=f"个股 {label} 对比（%）",
        labels={"year_quarter": "季度", col: f"{label}(%)", "name": "公司"},
        category_orders={"year_quarter": q_order},
        color_discrete_sequence=PALETTE,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(0,0,0,0.3)")
    return _style(fig, 430)


# ══════════════════════════════════════════════════════
# Section 4  行业下钻
# ══════════════════════════════════════════════════════

def plot_industry_rank_bar(df, metric, label, industry, quarter):
    """行业内公司排名 — 水平柱状"""
    sub = df[(df["industry"] == industry) & (df["year_quarter"] == quarter)].copy()
    sub["yi"] = sub[metric] / 1e8
    sub = sub.sort_values("yi", ascending=True)
    n = len(sub)

    fig = px.bar(
        sub, x="yi", y="name", orientation="h",
        title=f"{industry} — {label} 排名（{quarter}，亿元）",
        labels={"yi": f"{label}（亿元）", "name": ""},
        color="yi", color_continuous_scale="Blues",
    )
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    return _style(fig, max(280, n * 50 + 100))


def plot_industry_companies_trend(df, metric, label, industry, q_order):
    """行业内公司趋势 — 折线"""
    sub = df[df["industry"] == industry].copy()
    sub["yi"] = sub[metric] / 1e8

    fig = px.line(
        sub, x="year_quarter", y="yi", color="name", markers=True,
        title=f"{industry} — 公司 {label} 趋势（亿元）",
        labels={"year_quarter": "季度", "yi": f"{label}（亿元）", "name": "公司"},
        category_orders={"year_quarter": q_order},
        color_discrete_sequence=PALETTE,
    )
    return _style(fig, 400)