"""巨潮资讯公告抓取。

接口：akshare.stock_zh_a_disclosure_report_cninfo
- market: 沪深京
- category: 业绩预告 | 业绩快报 | 半年报 | 一季报 | 三季报 | 年报 ...
- start_date / end_date: YYYYMMDD

返回 DataFrame: 代码 / 简称 / 公告标题 / 公告时间 / 公告链接
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils.cache import JsonCache


def fetch_announcements(cfg: dict) -> pd.DataFrame:
    """从巨潮抓取指定时间窗内的披露公告。"""
    import akshare as ak  # 延迟导入，单元测试可不装 akshare

    start = cfg["resolved_start_date"]
    end = cfg["resolved_end_date"]
    market = cfg.get("market", "沪深京")
    category = cfg.get("disclosure", "业绩预告")
    keyword = cfg.get("keyword", "")
    raw_dir: Path = cfg["paths"]["raw_dir"]

    cache_path = raw_dir / f"announcements_{market}_{category}_{start}_{end}.json"
    raw_cache = JsonCache(cache_path)

    # akshare 接口只支持单 symbol；空 symbol = 全部
    df = ak.stock_zh_a_disclosure_report_cninfo(
        symbol="",
        market=market,
        keyword=keyword,
        category=category,
        start_date=start,
        end_date=end,
    )
    raw_cache.set("__meta__", {
        "market": market, "category": category, "start": start, "end": end,
        "rows": int(len(df)),
    })
    raw_cache.set("__df__", df.to_dict(orient="records"))
    raw_cache.save()
    return df
