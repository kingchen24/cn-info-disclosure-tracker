# Changelog

所有显著变更都会记录于此文件。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2026-07-16

### Added
- 首次公开版本
- 抓取巨潮"业绩预告"公告（沪深主板，可扩展到全部 A 股）
- 合并巨潮公司基本面 + 百度估值（PE-TTM / PE-静 / PB / 总市值）
- 输出带超链接的 Excel（含汇总 sheet）
- 磁盘 JSON 缓存，支持断点续抓
- YAML 配置 + CLI 参数双轨：换财报周期只改一个字段
