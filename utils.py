"""
utils.py — 通用工具函数与常量定义
"""
import pandas as pd
import numpy as np

# ==========================================
# 常量：核心指标英文字段 → 中文标签
# ==========================================
METRIC_LABELS = {
    "revenue":    "营业收入",
    "net_profit": "净利润",
    "capex":      "资本开支",
}


# ==========================================
# 数值格式化
# ==========================================
def format_number(value, unit="亿"):
    """将原始元数值格式化为亿元显示，带千分位"""
    if pd.isna(value) or value is None:
        return "N/A"
    if unit == "亿":
        return f"{value / 1e8:,.2f} 亿"
    elif unit == "万":
        return f"{value / 1e4:,.2f} 万"
    elif unit == "%":
        return f"{value:.2f}%"
    return f"{value:,.0f}"


def format_pct(value):
    """格式化百分比，带正负号"""
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{value:+.1f}%"


# ==========================================
# 季度排序工具
# ==========================================
def quarter_sort_key(yq: str) -> int:
    """'2024Q1' → 20241，用于排序"""
    try:
        return int(yq[:4]) * 10 + int(yq[-1])
    except (ValueError, IndexError):
        return 0


def sort_quarters(quarters) -> list:
    """对季度字符串列表排序"""
    return sorted(set(quarters), key=quarter_sort_key)


def get_prev_year_quarter(yq: str) -> str:
    """获取去年同季：'2025Q3' → '2024Q3'"""
    try:
        return f"{int(yq[:4]) - 1}Q{yq[-1]}"
    except (ValueError, IndexError):
        return ""