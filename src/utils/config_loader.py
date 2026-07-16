"""配置加载工具。

用法：
    from src.utils.config_loader import load_config
    cfg = load_config()
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_dates(cfg: dict) -> tuple[str, str]:
    """根据配置解析实际抓取的起止日期（YYYYMMDD）。

    - start_date / end_date 直接使用时优先
    - 否则用 end_date = 今天、start_date = 今天 - lookback_days
    """
    today = datetime.now()
    start = cfg.get("start_date")
    end = cfg.get("end_date")
    if start and end:
        return str(start), str(end)
    lookback = int(cfg.get("lookback_days", 30))
    end_dt = today
    start_dt = today - timedelta(days=lookback)
    return start_dt.strftime("%Y%m%d"), end_dt.strftime("%Y%m%d")


def load_config(path: str | os.PathLike | None = None) -> dict[str, Any]:
    """加载 YAML 配置，并注入派生字段。

    派生：
      - resolved_start_date / resolved_end_date
      - paths: data_raw_dir / cache_dir / output_xlsx / output_csv（绝对路径）
    """
    cfg_path = Path(path) if path else PROJECT_ROOT / "config" / "config.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    start, end = _resolve_dates(cfg)
    cfg["resolved_start_date"] = start
    cfg["resolved_end_date"] = end

    period = cfg.get("period", "")
    disc = cfg.get("disclosure", "")
    board = cfg.get("board_filter", "")
    out = cfg.get("output", {}) or {}
    raw_dir = PROJECT_ROOT / out.get("raw_dir", "data/raw")
    cache_dir = PROJECT_ROOT / out.get("cache_dir", "data/cache")
    xlsx_tpl = out.get("xlsx", "output/{period}_{disclosure}_{board_filter}_{start_date}_{end_date}.xlsx")
    csv_tpl = out.get("summary_csv", "output/{period}_{disclosure}_{board_filter}_summary.csv")
    cfg["paths"] = {
        "raw_dir": raw_dir,
        "cache_dir": cache_dir,
        "xlsx": PROJECT_ROOT / xlsx_tpl.format(
            period=period, disclosure=disc, board_filter=board,
            start_date=start, end_date=end,
        ),
        "summary_csv": PROJECT_ROOT / csv_tpl.format(
            period=period, disclosure=disc, board_filter=board,
            start_date=start, end_date=end,
        ),
    }
    for p in (raw_dir, cache_dir, cfg["paths"]["xlsx"].parent, cfg["paths"]["summary_csv"].parent):
        p.mkdir(parents=True, exist_ok=True)
    return cfg
