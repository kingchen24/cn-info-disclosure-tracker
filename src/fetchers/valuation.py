"""估值数据抓取（默认百度股市通）。

akshare 接口：stock_zh_valuation_baidu
- symbol: 6 位代码
- indicator: 市盈率(TTM) / 市盈率(静) / 市净率 / 总市值
- period: 近一年（拿最后一日 = 最新数据）

并发抓取 + 磁盘缓存。
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

from src.utils.cache import JsonCache, retry


def _fetch_one(code: str, indicators: list[str]) -> tuple[str, dict]:
    import akshare as ak

    out: dict[str, float] = {}
    for ind in indicators:
        try:
            df = retry(
                lambda: ak.stock_zh_valuation_baidu(
                    symbol=code, indicator=ind, period="近一年"
                ),
                attempts=2, sleep=0.3,
            )
            if len(df):
                out[ind] = float(df["value"].iloc[-1])
        except Exception as e:  # noqa: BLE001
            out[f"{ind}__error__"] = str(e)
    return code, out


def fetch_valuations(codes: Iterable[str], cfg: dict) -> dict[str, dict]:
    cache_path: Path = cfg["paths"]["cache_dir"] / "valuations.json"
    cache = JsonCache(cache_path)

    indicators = cfg.get("valuation_indicators", ["市盈率(TTM)", "市盈率(静)", "市净率", "总市值"])
    workers = int(cfg.get("concurrency", {}).get("valuation_workers", 6))

    todos = [c for c in codes if not cache.has(c)]
    if todos:
        print(f"[valuation] 待抓取 {len(todos)} / 缓存命中 {len(codes) - len(todos)}")

    if todos:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_fetch_one, c, indicators): c for c in todos}
            done = 0
            for fut in as_completed(futs):
                code, payload = fut.result()
                cache.set(code, payload)
                done += 1
                if done % 30 == 0:
                    cache.save()
                    print(f"[valuation] {done}/{len(todos)} 已缓存")
        cache.save()
    return {c: cache.get(c) or {} for c in codes}
