# 使用细节

## 运行流程图

```
config/config.yaml
        │
        ▼
   load_config()  ────► 解析日期/路径
        │
        ▼
fetch_announcements()  ──► 巨潮 API ──► data/raw/*.json
        │
        ▼
filter_by_board()  ──► 主板过滤
        │
        ▼
fetch_profiles()  ──► 巨潮 webapi ──► data/cache/profiles.json
        │
        ▼
fetch_valuations()  ──► 百度 ──► data/cache/valuations.json
        │
        ▼
build_table()  ──► 三表 join + 字段对齐
        │
        ▼
export()  ──► output/*.xlsx
```

## 缓存策略

- `data/raw/announcements_*.json` ：原始公告抓取结果（每次跑都会重新拉，按文件覆盖）
- `data/cache/profiles.json` ：按股票代码缓存；下次启动自动复用
- `data/cache/valuations.json` ：按股票代码缓存

要强制全量重抓，删除对应 `data/cache/` 文件即可：

```bash
rm -rf data/cache/*.json
```

## 切换数据源

### 估值改用东方财富

`config/config.yaml`：

```yaml
valuation_source: eastmoney
```

> 注意：东方财富 push2 接口容易被限速，需自行加代理或降低 `concurrency.valuation_workers`。

## CLI 参数优先级

CLI 参数 > YAML 配置 > 默认值。

例：

```bash
# YAML 里配的是半年报，本次只跑一季报
python -m src.main --period 一季报 --start 20260401 --end 20260430
```

## 异常与重试

- 单只股票 profile 抓取失败：自动重试 3 次；最终失败会写入 `{"__error__": "..."}` 占位
- 估值抓取失败：每个 indicator 单独重试 2 次
- akshare 整体不可用：抛出 `ConnectionError`，缓存中已有数据不受影响
