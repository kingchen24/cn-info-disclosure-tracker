"""公司基本面（巨潮 stock_profile_cninfo）批量抓取 + 缓存。"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.utils.cache import JsonCache, retry


def fetch_profiles(codes: Iterable[str], cfg: dict) -> dict[str, dict]:
    """返回 {code: profile_dict}。

    profile_dict 字段（来自巨潮）：
      公司名称 / 英文名称 / 曾用简称 / A股代码 / A股简称 / 所属市场 / 所属行业 /
      法人代表 / 注册资金 / 成立日期 / 上市日期 / 注册地址 / 办公地址 /
      主营业务 / 经营范围 / 机构简介 ...
    """
    import akshare as ak  # noqa: F401 - 延迟导入

    cache_path: Path = cfg["paths"]["cache_dir"] / "profiles.json"
    cache = JsonCache(cache_path)

    todos = [c for c in codes if not cache.has(c)]
    if todos:
        print(f"[profiles] 待抓取 {len(todos)} / 缓存命中 {len(codes) - len(todos)}")
    for i, code in enumerate(todos, 1):
        try:
            df = retry(ak.stock_profile_cninfo, symbol=code, attempts=3, sleep=0.6)
            if len(df):
                cache.set(code, df.iloc[0].to_dict())
            else:
                cache.set(code, {})
        except Exception as e:  # noqa: BLE001
            cache.set(code, {"__error__": str(e)})
        if i % 50 == 0:
            cache.save()
            print(f"[profiles] {i}/{len(todos)} 已缓存")
        # 串行模式：避免 mini_racer.dll 多线程崩溃
        time.sleep(0.02)
    cache.save()
    return {c: cache.get(c) or {} for c in codes}
