"""项目主入口。

流程：
    1. 加载 config/config.yaml
    2. 抓取公告（巨潮）
    3. 按板块过滤
    4. 抓取公司基本面（巨潮 profile）
    5. 抓取估值（百度 / 东财）
    6. 合并、生成 Excel
    7. 打印汇总

示例：
    python -m src.main
    python -m src.main --config config/config.yaml
    python -m src.main --period 年报 --disclosure 业绩预告
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# 把项目根目录加入 sys.path，使 ``python src/main.py`` 也能运行
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.fetchers.announcements import fetch_announcements
from src.fetchers.profiles import fetch_profiles
from src.fetchers.valuation import fetch_valuations
from src.pipelines.export_excel import export
from src.pipelines.merge import build_table, summary
from src.utils.board_filter import filter_by_board
from src.utils.config_loader import load_config


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="A 股财报披露跟踪")
    p.add_argument("--config", default="config/config.yaml", help="配置文件路径")
    p.add_argument("--period", help="覆盖配置: 一季报 | 半年报 | 三季报 | 年报")
    p.add_argument("--disclosure", help="覆盖配置: 业绩预告 | 业绩快报 | ...")
    p.add_argument("--start", help="覆盖配置起始日期 YYYYMMDD")
    p.add_argument("--end", help="覆盖配置结束日期 YYYYMMDD")
    p.add_argument("--board", help="覆盖配置: 主板 | 主板+创业板 | 全部 A 股")
    return p.parse_args()


def apply_overrides(cfg: dict, args: argparse.Namespace) -> dict:
    if args.period: cfg["period"] = args.period
    if args.disclosure: cfg["disclosure"] = args.disclosure
    if args.board: cfg["board_filter"] = args.board
    if args.start: cfg["start_date"] = args.start
    if args.end: cfg["end_date"] = args.end
    # 重新解析派生字段
    return load_config(args.config)


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    cfg = apply_overrides(cfg, args)

    print("=" * 70)
    print(f"  {cfg['period']} {cfg['disclosure']}  |  {cfg['board_filter']}  |  "
          f"{cfg['resolved_start_date']} ~ {cfg['resolved_end_date']}")
    print("=" * 70)

    # 1. 公告
    announcements = fetch_announcements(cfg)
    print(f"[1/4] 公告原始条数: {len(announcements)}")

    # 2. 板块过滤
    keep_codes = filter_by_board(announcements["代码"].tolist(), cfg)
    announcements = announcements[announcements["代码"].isin(keep_codes)].copy()
    print(f"[2/4] 板块过滤后: {len(announcements)} 条  / 独立股票: {announcements['代码'].nunique()}")

    if announcements.empty:
        print("⚠ 范围内没有符合条件的公告，无需后续步骤。")
        return 0

    codes = announcements["代码"].unique().tolist()

    # 3. 基本面 + 估值（带磁盘缓存）
    profiles = fetch_profiles(codes, cfg)
    valuations = fetch_valuations(codes, cfg)

    # 4. 合并 + 导出
    df = build_table(announcements, profiles, valuations, cfg)
    summary_dfs = summary(df)
    export(df, summary_dfs, cfg["paths"]["xlsx"], cfg)
    df.to_csv(cfg["paths"]["summary_csv"].with_name(
        cfg["paths"]["summary_csv"].stem + "_detail.csv"
    ), index=False, encoding="utf-8-sig")

    print()
    print(f"[OK] Excel:  {cfg['paths']['xlsx']}")
    print(f"[OK] Detail: {cfg['paths']['summary_csv'].with_name(cfg['paths']['summary_csv'].stem + '_detail.csv')}")
    print()
    print("行业 Top 10：")
    print(summary_dfs["industry"].head(10).to_string(index=False))
    print()
    print("板块分布：")
    print(summary_dfs["market"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
