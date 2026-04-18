"""
data_loader.py — 数据加载、清洗与示例数据生成
"""
import os
import io
import pandas as pd
import numpy as np
import streamlit as st


# ==========================================
# 内部：数据清洗流水线
# ==========================================
def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    数据清洗与特征工程：
    1. 解析日期  2. 提取年/季度  3. 数值转换
    4. 排序  5. 缺失值处理
    """
    df = df.copy()

    # ① 解析日期
    df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
    df = df.dropna(subset=["report_date"])

    # ② 年份 / 季度 / 年季度标签
    df["year"]    = df["report_date"].dt.year
    df["quarter"] = df["report_date"].dt.quarter
    df["year_quarter"] = df["year"].astype(str) + "Q" + df["quarter"].astype(str)

    # ③ 数值列强制转换
    for col in ["revenue", "net_profit", "capex", "market_cap"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ④ 按公司+日期排序
    df = df.sort_values(["ts_code", "report_date"]).reset_index(drop=True)

    # ⑤ 填充缺失的文本字段
    if "name" in df.columns:
        df["name"] = df["name"].fillna(df["ts_code"])
    if "industry" in df.columns:
        df["industry"] = df["industry"].fillna("未分类")

    return df


# ==========================================
# 对外接口
# ==========================================
@st.cache_data(show_spinner="正在加载数据...")
def load_data(file_path: str = "data/financial_data.csv") -> pd.DataFrame:
    """读取 CSV；文件不存在时自动使用内置示例数据"""
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        df = generate_sample_data()
    return _clean_data(df)


@st.cache_data(show_spinner="正在解析上传文件...")
def load_data_from_bytes(raw: bytes) -> pd.DataFrame:
    """从上传文件的字节流加载"""
    df = pd.read_csv(io.BytesIO(raw))
    return _clean_data(df)


# ==========================================
# 示例数据生成器（10 家公司 × 8 季度 = 80 行）
# ==========================================
def generate_sample_data() -> pd.DataFrame:
    """生成模拟 A 股季度财务数据，金额单位：元"""
    np.random.seed(42)

    companies = [
        ("600519.SH", "贵州茅台", "白酒"),
        ("000858.SZ", "五粮液",   "白酒"),
        ("000568.SZ", "泸州老窖", "白酒"),
        ("300750.SZ", "宁德时代", "新能源"),
        ("601012.SH", "隆基绿能", "新能源"),
        ("002594.SZ", "比亚迪",   "汽车"),
        ("601238.SH", "广汽集团", "汽车"),
        ("000333.SZ", "美的集团", "家电"),
        ("000651.SZ", "格力电器", "家电"),
        ("600036.SH", "招商银行", "银行"),
    ]

    quarters = [
        "2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31",
        "2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31",
    ]

    # 每家公司的季度基础数据（单位：元）
    bases = {
        "600519.SH": dict(revenue=350e8, net_profit=170e8, capex=15e8,  market_cap=22000e8),
        "000858.SZ": dict(revenue=200e8, net_profit=75e8,  capex=10e8,  market_cap=7000e8),
        "000568.SZ": dict(revenue=75e8,  net_profit=32e8,  capex=5e8,   market_cap=3500e8),
        "300750.SZ": dict(revenue=850e8, net_profit=105e8, capex=80e8,  market_cap=10000e8),
        "601012.SH": dict(revenue=220e8, net_profit=22e8,  capex=38e8,  market_cap=1500e8),
        "002594.SZ": dict(revenue=1500e8,net_profit=70e8,  capex=120e8, market_cap=8000e8),
        "601238.SH": dict(revenue=280e8, net_profit=12e8,  capex=25e8,  market_cap=1200e8),
        "000333.SZ": dict(revenue=900e8, net_profit=82e8,  capex=35e8,  market_cap=4500e8),
        "000651.SZ": dict(revenue=480e8, net_profit=55e8,  capex=18e8,  market_cap=2200e8),
        "600036.SH": dict(revenue=880e8, net_profit=380e8, capex=22e8,  market_cap=9500e8),
    }

    rows = []
    for ts_code, name, industry in companies:
        b = bases[ts_code]
        for i, qd in enumerate(quarters):
            # 趋势 + 季节性 + 随机噪声
            trend    = 1 + 0.02 * i
            seasonal = 1 + 0.06 * np.sin(i * np.pi / 2)
            noise    = max(np.random.normal(1.0, 0.05), 0.75)
            factor   = trend * seasonal * noise

            rows.append(dict(
                report_date = qd,
                ts_code     = ts_code,
                name        = name,
                industry    = industry,
                revenue     = round(b["revenue"]    * factor),
                net_profit  = round(b["net_profit"]  * factor * np.random.normal(1, 0.08)),
                capex       = round(b["capex"]       * factor * np.random.normal(1, 0.10)),
                market_cap  = round(b["market_cap"]  * (1 + 0.015 * i) * np.random.normal(1, 0.06)),
            ))

    return pd.DataFrame(rows)