"""生成一份示例 Excel，用于 README 截图 / 本地预览。

特点：
- 不用联网，全用 mock 数据
- 包含多种预告类型（预增 / 预减 / 扭亏 / 亏损）、不同行业、不同板块
- 同时输出汇总 sheet
- 文件落到 output/sample.xlsx（已在 .gitignore）
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipelines.export_excel import export
from src.pipelines.merge import build_table, summary

random.seed(7)

INDUSTRIES = [
    "酒、饮料和精制茶制造业",
    "货币金融服务业",
    "汽车制造业",
    "计算机、通信和其他电子设备制造业",
    "医药制造业",
    "房地产业",
    "电气机械和器材制造业",
    "化学原料和化学制品制造业",
    "软件和信息技术服务业",
    "电力、热力生产和供应业",
]

MAIN_BUSINESS = [
    "主营新能源电池研发、生产与销售。",
    "城市商业银行，业务涵盖存贷款、结算、投行。",
    "整车制造及上下游零部件研发与销售。",
    "半导体设备及零部件研发生产销售。",
    "创新药研发、生产与商业化。",
    "商品住宅及商业地产开发。",
    "变压器、开关柜等输配电设备。",
    "精细化工产品生产与销售。",
    "金融科技解决方案。",
    "火力发电及新能源运营。",
]

ANNOUNCEMENT_TYPES = [
    ("2026年半年度业绩预告", "预增", "净利润同比增长 80%–110%"),
    ("2026年半年度业绩预告", "预减", "净利润同比下降 50%–70%"),
    ("2026年半年度业绩预告", "扭亏", "净利润扭亏为盈"),
    ("2026年半年度业绩预告", "首亏", "预计净利润为负值"),
    ("2026年半年度业绩预告", "略增", "净利润同比增长 10%–30%"),
    ("2026年半年度业绩预告", "略减", "净利润同比下降 10%–30%"),
    ("2026年半年度业绩预告", "续盈", "净利润为正值"),
    ("2026年半年度业绩预告", "续亏", "连续亏损"),
    ("2026年半年度业绩预告", "不确定", "财务核算未完成"),
]

CODES_MAIN_SH = ["600519", "600036", "601318", "601398", "601988", "600276", "600030", "600887"]
CODES_MAIN_SZ = ["000001", "000002", "000333", "000651", "000858", "002594", "002475", "003012"]
CODES_CREATIVE = ["300750", "300760", "301308"]  # 测试过滤

rows = []
all_codes = CODES_MAIN_SH + CODES_MAIN_SZ + CODES_CREATIVE
for i, code in enumerate(all_codes):
    name = {"600519":"贵州茅台","600036":"招商银行","601318":"中国平安","601398":"工商银行",
            "601988":"中国银行","600276":"恒瑞医药","600030":"中信证券","600887":"伊利股份",
            "000001":"平安银行","000002":"万科A","000333":"美的集团","000651":"格力电器",
            "000858":"五粮液","002594":"比亚迪","002475":"立讯精密","003012":"东鹏控股",
            "300750":"宁德时代","300760":"迈瑞医疗","301308":"江波龙"}[code]
    industry = INDUSTRIES[i % len(INDUSTRIES)]
    business = MAIN_BUSINESS[i % len(MAIN_BUSINESS)]
    title, ann_type, hint = ANNOUNCEMENT_TYPES[i % len(ANNOUNCEMENT_TYPES)]
    pe_ttm = round(random.uniform(-50, 50), 2) if random.random() > 0.05 else None
    pe_static = round(pe_ttm * random.uniform(0.9, 1.1), 2) if pe_ttm is not None else None
    pb = round(random.uniform(0.3, 8), 2)
    mv = round(random.uniform(30, 15000), 2)
    rows.append({
        "代码": code, "简称": name,
        "公告标题": f"{title}（{ann_type}）",
        "公告时间": pd.Timestamp("2026-07-15") - pd.Timedelta(days=i % 14),
        "公告链接": f"http://www.cninfo.com.cn/new/disclosure/detail?stockCode={code}",
    })
    # 同步给到 profiles / valuations
ann = pd.DataFrame(rows)

# 板块过滤
from src.utils.board_filter import filter_by_board
cfg = {
    "period": "半年报", "disclosure": "业绩预告", "board_filter": "主板",
    "main_board_prefixes": ["600","601","603","605","000","001","002","003"],
    "exclude_prefixes": ["688","300","301","8","4","9"],
}
keep = filter_by_board(ann["代码"].tolist(), cfg)
ann = ann[ann["代码"].isin(keep)].copy()

profiles = {}
valuations = {}
for _, r in ann.iterrows():
    code = r["代码"]
    profiles[code] = {
        "公司名称": f"{r['简称']}股份有限公司",
        "所属市场": "上交所" if code.startswith(("600","601","603","605")) else "深交所主板",
        "所属行业": INDUSTRIES[hash(code) % len(INDUSTRIES)],
        "上市日期": f"19{random.randint(85,99)}-0{random.randint(1,9)}-{random.randint(10,28):02d}",
        "主营业务": MAIN_BUSINESS[hash(code) % len(MAIN_BUSINESS)],
    }
    pe_ttm = round(random.uniform(-30, 60), 2)
    valuations[code] = {
        "市盈率(TTM)": pe_ttm,
        "市盈率(静)": round(pe_ttm * random.uniform(0.9, 1.1), 2),
        "市净率": round(random.uniform(0.3, 8), 2),
        "总市值": round(random.uniform(30, 15000), 2),
    }

df = build_table(ann, profiles, valuations, cfg)
out = ROOT / "output" / "sample.xlsx"
export(df, summary(df), out, cfg)
print(f"[OK] {out}  rows={len(df)}")
