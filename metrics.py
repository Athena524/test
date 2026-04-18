"""
metrics.py — 财务指标计算模块
包含：同比 (YoY)、环比 (QoQ)、行业汇总、市场分位数、TTM
"""
import pandas as pd
import numpy as np


def add_growth_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    为 DataFrame 添加三个核心指标的同比 / 环比增长率列。

    计算逻辑（以 revenue 为例）：
      revenue_yoy = (当季 - 去年同季) / |去年同季| × 100
      revenue_qoq = (当季 - 上一季)  / |上一季|  × 100

    使用绝对值作分母，避免基数为负时符号错误。
    """
    df = df.sort_values(["ts_code", "report_date"]).copy()

    for metric in ["revenue", "net_profit", "capex"]:
        if metric not in df.columns:
            continue

        # ---- 同比 YoY：与同一公司 4 个季度前比较 ----
        prev4 = df.groupby("ts_code")[metric].shift(4)
        df[f"{metric}_yoy"] = np.where(
            prev4.abs() > 0,
            (df[metric] - prev4) / prev4.abs() * 100,
            np.nan,
        )

        # ---- 环比 QoQ：与同一公司 1 个季度前比较 ----
        prev1 = df.groupby("ts_code")[metric].shift(1)
        df[f"{metric}_qoq"] = np.where(
            prev1.abs() > 0,
            (df[metric] - prev1) / prev1.abs() * 100,
            np.nan,
        )

    return df


def compute_industry_summary(
    df: pd.DataFrame, metric: str, quarter: str
) -> pd.DataFrame:
    """指定季度的行业汇总统计（合计 / 均值 / 中位数 / 公司数）"""
    qdf = df[df["year_quarter"] == quarter]
    if qdf.empty:
        return pd.DataFrame(columns=["行业", "合计", "均值", "中位数", "公司数"])

    summary = (
        qdf.groupby("industry")
        .agg(合计=(metric, "sum"), 均值=(metric, "mean"),
             中位数=(metric, "median"), 公司数=(metric, "count"))
        .reset_index()
        .rename(columns={"industry": "行业"})
        .sort_values("合计", ascending=False)
        .reset_index(drop=True)
    )
    return summary


def compute_market_percentile(df: pd.DataFrame, metric: str) -> pd.Series:
    """每家公司在当季度的市场分位数 (0‒100)"""
    return df.groupby("year_quarter")[metric].rank(pct=True) * 100


def compute_ttm(df: pd.DataFrame, metric: str) -> pd.Series:
    """TTM（滚动 4 季度合计），按公司分组"""
    df = df.sort_values(["ts_code", "report_date"])
    return df.groupby("ts_code")[metric].transform(
        lambda s: s.rolling(4, min_periods=4).sum()
    )