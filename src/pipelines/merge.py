"""合并公告/基本面/估值三份数据，处理字段错位并标准化输出。"""
from __future__ import annotations

from typing import Iterable

import pandas as pd

from src.utils.board_filter import classify_board


def _fix_profile_misalignment(code: str, profile: dict) -> tuple[str, str, str]:
    """部分股票（已知 000151 等）巨潮返回字段会错位：所属行业 ↔ 所属市场。

    返回 (market, industry, full_name)，尽量使用原始字段，只有在明显错位时才纠正。
    """
    market_raw = (profile.get("所属市场") or "").strip()
    industry_raw = (profile.get("所属行业") or "").strip()
    name = (profile.get("公司名称") or "").strip()

    # 推断的"真实"所属市场
    inferred_market = classify_board(code, [], [])
    # 若原始字段不是标准市场名（如 "批发业"），认为是错位
    valid_markets = {"上交所主板", "深交所主板", "上交所", "深交所", "北交所", "其他"}
    if market_raw not in valid_markets:
        market_fixed = inferred_market if inferred_market != "其他" else market_raw
    else:
        market_fixed = market_raw

    # 若"所属行业"看起来是入选指数（包含 '指' / 顿号 / 数字），而所属市场看起来像行业
    looks_like_index = (
        "," in industry_raw
        or "指" in industry_raw
        or industry_raw.startswith(("国证", "中证", "上证", "深证", "沪深"))
    )
    looks_like_industry = ("业" in market_raw) and len(market_raw) <= 12
    if looks_like_index and looks_like_industry:
        industry_fixed = market_raw
    else:
        industry_fixed = industry_raw
    return market_fixed, industry_fixed, name


def build_table(
    announcements: pd.DataFrame,
    profiles: dict[str, dict],
    valuations: dict[str, dict],
    cfg: dict,
) -> pd.DataFrame:
    """合并三个数据源，输出统一长表 DataFrame。

    去重：同一只股票若有多条公告，保留最早一条（最严的预告口径）。
    """
    if announcements.empty:
        return pd.DataFrame()

    df = announcements.copy()
    df["公告时间"] = pd.to_datetime(df["公告时间"], errors="coerce")
    df = df.sort_values(["代码", "公告时间"]).drop_duplicates("代码", keep="first")

    rows = []
    for _, r in df.iterrows():
        code = r["代码"]
        prof = profiles.get(code) or {}
        market, industry, full_name = _fix_profile_misalignment(code, prof)
        val = valuations.get(code) or {}

        biz = (prof.get("主营业务") or "")
        rows.append({
            "股票代码": code,
            "股票简称": r.get("简称", ""),
            "公司全称": full_name,
            "所属市场": market,
            "所属行业": industry,
            "上市日期": prof.get("上市日期", ""),
            "主营业务简介": biz[:200] if biz else "",
            "市盈率-静": val.get("市盈率(静)"),
            "市盈率-TTM": val.get("市盈率(TTM)"),
            "市净率": val.get("市净率"),
            "总市值(亿元)": val.get("总市值"),
            "公告标题": r.get("公告标题", ""),
            "公告时间": r.get("公告时间", ""),
            "公告链接": r.get("公告链接", ""),
        })
    out = pd.DataFrame(rows)

    # 按行业、代码排序，方便阅读
    out = out.sort_values(["所属行业", "股票代码"]).reset_index(drop=True)
    out.insert(0, "序号", range(1, len(out) + 1))
    return out


def summary(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """生成汇总统计。"""
    return {
        "industry": df["所属行业"].value_counts().rename_axis("所属行业").reset_index(name="股票数"),
        "market": df["所属市场"].value_counts().rename_axis("所属市场").reset_index(name="股票数"),
    }
