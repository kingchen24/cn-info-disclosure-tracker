"""端到端 smoke 测试：使用 mock 数据验证 pipeline。

不需要网络，可随时跑：``python -m tests.test_merge``。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipelines.export_excel import export
from src.pipelines.merge import build_table, summary


def make_fake() -> tuple[pd.DataFrame, dict, dict]:
    ann = pd.DataFrame([
        {"代码": "600519", "简称": "贵州茅台", "公告标题": "2026年半年度业绩预告",
         "公告时间": pd.Timestamp("2026-07-15"),
         "公告链接": "http://example.com/600519"},
        {"代码": "000001", "简称": "平安银行", "公告标题": "2026年半年度业绩预告",
         "公告时间": pd.Timestamp("2026-07-15"),
         "公告链接": "http://example.com/000001"},
        {"代码": "002594", "简称": "比亚迪", "公告标题": "2026年半年度业绩预告",
         "公告时间": pd.Timestamp("2026-07-15"),
         "公告链接": "http://example.com/002594"},
        {"代码": "300750", "简称": "宁德时代", "公告标题": "2026年半年度业绩预告",
         "公告时间": pd.Timestamp("2026-07-15"),
         "公告链接": "http://example.com/300750"},
        # 错位样例（000151）
        {"代码": "000151", "简称": "中成股份", "公告标题": "2026年半年度业绩预告",
         "公告时间": pd.Timestamp("2026-07-15"),
         "公告链接": "http://example.com/000151"},
    ])

    profiles = {
        "600519": {"公司名称": "贵州茅台酒股份有限公司",
                   "所属市场": "上交所", "所属行业": "酒、饮料和精制茶制造业",
                   "上市日期": "2001-08-27",
                   "主营业务": "贵州茅台酒系列产品的产品研制、酿造生产、包装和销售。"},
        "000001": {"公司名称": "平安银行股份有限公司",
                   "所属市场": "深交所主板", "所属行业": "货币金融服务业",
                   "上市日期": "1991-04-03",
                   "主营业务": "人民币、外币存贷款及国际、国内结算业务。"},
        "002594": {"公司名称": "比亚迪股份有限公司",
                   "所属市场": "深交所主板", "所属行业": "汽车制造业",
                   "上市日期": "2011-06-30",
                   "主营业务": "新能源汽车、传统燃油汽车及动力电池等业务。"},
        "300750": {"公司名称": "宁德时代新能源科技股份有限公司",
                   "所属市场": "深交所", "所属行业": "电气机械和器材制造业",
                   "上市日期": "2018-06-11",
                   "主营业务": "动力电池、储能电池和电池回收等。"},
        "000151": {"公司名称": "中成进出口股份有限公司",
                   "所属市场": "批发业",        # 错位：实际应是行业
                   "所属行业": "国证Ａ指,中证央企",  # 错位：实际是入选指数
                   "上市日期": "2000-09-06",
                   "主营业务": "成套设备出口和国际工程承包。"},
    }
    valuations = {
        "600519": {"市盈率(TTM)": 18.91, "市盈率(静)": 19.0, "市净率": 5.77, "总市值": 15639.27},
        "000001": {"市盈率(TTM)": 4.89, "市盈率(静)": 5.1, "市净率": 0.46, "总市值": 2103.6},
        "002594": {"市盈率(TTM)": 30.37, "市盈率(静)": 31.5, "市净率": 3.61, "总市值": 8365.94},
        "300750": {"市盈率(TTM)": 22.5, "市盈率(静)": 23.0, "市净率": 4.2, "总市值": 11000.0},
        "000151": {"市盈率(TTM)": 15.0, "市盈率(静)": 14.5, "市净率": 1.2, "总市值": 35.0},
    }
    return ann, profiles, valuations


def main() -> int:
    ann, profiles, valuations = make_fake()
    cfg = {
        "period": "半年报",
        "disclosure": "业绩预告",
        "board_filter": "主板",
        "main_board_prefixes": ["600", "601", "603", "605", "000", "001", "002", "003"],
        "exclude_prefixes": ["688", "300", "301", "8", "4", "9"],
    }

    # 板块过滤
    from src.utils.board_filter import filter_by_board
    keep = filter_by_board(ann["代码"].tolist(), cfg)
    ann = ann[ann["代码"].isin(keep)].copy()
    print("after board filter:", ann["代码"].tolist())
    assert "300750" not in ann["代码"].tolist(), "创业板应被过滤"

    df = build_table(ann, profiles, valuations, cfg)
    print(df[["序号", "股票代码", "股票简称", "所属市场", "所属行业"]].to_string(index=False))
    # 错位修正
    row = df[df["股票代码"] == "000151"].iloc[0]
    assert row["所属行业"] == "批发业", f"000151 行业应修正为 批发业, got {row['所属行业']}"
    assert row["所属市场"] == "深交所主板", f"000151 市场应为 深交所主板, got {row['所属市场']}"

    summary_dfs = summary(df)
    out = ROOT / "output" / "smoke_test.xlsx"
    export(df, summary_dfs, out, cfg)
    print(f"\n[OK] wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
