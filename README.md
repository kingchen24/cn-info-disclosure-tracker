# A 股财报披露跟踪 (cn-info-disclosure-tracker)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![akshare](https://img.shields.io/badge/data-akshare%20%2B%20baidu-1f6feb)

针对 **沪深主板**上市公司，抓取指定时间窗口内发布的**半年报 / 一季报 / 三季报 / 年报业绩预告**公告，合并公司基本面（所属行业、主营业务、上市日期）与当日估值（市盈率-TTM / 市盈率-静 / 市净率 / 总市值），输出一份带超链接的 Excel 表格，方便快速分类、排序与回溯。

> 下次财报周期只需要改一个 YAML 字段即可复用。

---

## ✨ 功能

- 📑 **披露公告抓取**：巨潮资讯网 `业绩预告` / `业绩快报` 等类别，按时间窗批量拉取
- 🏭 **板块过滤**：主板 / 主板+创业板 / 全部 A 股 一键切换
- 🏢 **公司基本面**：全称、所属行业（证监会分类）、上市日期、主营业务简介
- 💹 **估值快照**：市盈率-TTM、市盈率-静、市净率、总市值（百度股市通 2026-07-15 数据）
- 🔗 **公告链接**：每行末尾的"公告链接"列直接指向巨潮披露详情页
- 💾 **磁盘缓存**：抓取中途断网 / 重跑脚本会复用 `data/cache/`，不会重复请求
- 📊 **汇总 sheet**：行业分布、板块分布

---

## 📁 项目结构

```
.
├── config/
│   └── config.yaml           # 所有可调参数（周期、起止日、板块、并发等）
├── src/
│   ├── main.py               # 入口（python -m src.main）
│   ├── fetchers/
│   │   ├── announcements.py  # 巨潮公告
│   │   ├── profiles.py       # 公司基本面
│   │   └── valuation.py      # 估值（百度）
│   ├── pipelines/
│   │   ├── merge.py          # 三表合并、字段对齐
│   │   └── export_excel.py   # 美化输出
│   └── utils/
│       ├── config_loader.py  # YAML 加载 + 派生字段
│       ├── board_filter.py   # 主板/创业板/科创板/北交所 分类
│       └── cache.py          # JSON 磁盘缓存
├── data/
│   ├── raw/                  # 原始公告抓取结果
│   └── cache/                # profile / valuation 缓存
├── output/                   # 生成的 .xlsx 与 csv
├── releases/                 # (GitHub Release) 每个周期的发布产物
├── docs/
│   └── CHANGELOG.md
├── tests/                    # 占位，后续补单元测试
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

> `mini-racer`（akshare 间接依赖）需要 Windows 上有 Visual C++ Redistributable；Linux/Mac 通常自带。

### 2. 调整配置（关键）

打开 `config/config.yaml`，按需修改：

```yaml
period: 半年报            # 一季报 | 半年报 | 三季报 | 年报
disclosure: 业绩预告       # 业绩预告 | 业绩快报
start_date: 20260615      # YYYYMMDD；设为 null 时启用 lookback_days
end_date:   20260715
lookback_days: 30
board_filter: 主板         # 主板 | 主板+创业板 | 全部 A 股
valuation_source: baidu    # baidu（默认） | eastmoney
```

或者直接用命令行参数覆盖（不影响配置文件）：

```bash
python -m src.main --period 年报 --disclosure 业绩快报 --start 20270101 --end 20270201
```

### 3. 运行

```bash
python -m src.main
```

输出：

```
[OK] Excel:  output/半年报_业绩预告_主板_20260615_20260715.xlsx
[OK] Detail: output/半年报_业绩预告_主板_summary_detail.csv
```

第一次运行约 30-40 分钟（akshare 串行抓 1200 只 profile 是瓶颈）。
**重跑速度极快**：所有抓取结果会写进 `data/cache/`，下次直接读缓存。

### 4. 上传到 GitHub Release

每个财报周期生成的 Excel 适合作为 Release 产物：

```bash
gh release create v2026H1 \
    output/半年报_业绩预告_主板_20260615_20260715.xlsx \
    --title "2026 半年报业绩预告（主板）"
```

---

## 🧭 下次怎么用（同一周期再跑）

```bash
# 1. 修改 config/config.yaml
#    period: 年报
#    disclosure: 业绩预告
#    start_date: 20270101
#    end_date:   20270201
# 2. 跑
python -m src.main
# 3. 把 output/ 里的 xlsx 上传到 GitHub Release
```

---

## 🔧 数据源说明

| 数据 | 来源 | 接口 |
|---|---|---|
| 公告列表 | 巨潮资讯网 | `akshare.stock_zh_a_disclosure_report_cninfo` |
| 公司基本面 | 巨潮 webapi | `akshare.stock_profile_cninfo` |
| 估值 | 百度股市通 | `akshare.stock_zh_valuation_baidu` |

> **为什么不用东方财富 push2 接口？** 该接口在本网络环境下高频请求易触发 RemoteDisconnected。改用百度接口更稳定。

---

## ⚠️ 已知限制

- 公告**类型**（预增/预减/略增/略减/扭亏/续亏/首亏/不确定）只在公告正文里出现，本表标题统一是"XX 公司 2026 年半年度业绩预告"，因此未在表格中强行打标。可按需扩展 `src/fetchers/announcements.py` 拉正文解析。
- 估值指标在某些新股次新 / 亏损股上为负数或缺失，保留原值以便排查。
- 个别股票（已知 000151 等）巨潮返回字段会错位，`src/pipelines/merge.py` 已做"所属行业↔所属市场"启发式修正。

---

## 📜 License

[MIT](LICENSE)
