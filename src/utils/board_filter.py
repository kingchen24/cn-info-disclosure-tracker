"""板块过滤工具：根据 config.yaml 的前缀列表判断一只股票是否属于主板。

支持 ``board_filter`` 取值：
- ``主板``        : 只保留 main_board_prefixes 命中的代码
- ``主板+创业板``: 主板 + 创业板前缀（300/301）
- ``全部 A 股``  : 不过滤
"""
from __future__ import annotations


def classify_board(code: str, prefixes: list[str], exclude: list[str]) -> str:
    """返回 '沪市主板' / '深市主板' / '创业板' / '科创板' / '北交所' / '其他'。"""
    if code.startswith(("600", "601", "603", "605")):
        return "沪市主板"
    if code.startswith(("000", "001", "002", "003")):
        return "深交所主板"
    if code.startswith(("300", "301")):
        return "创业板"
    if code.startswith("688"):
        return "科创板"
    if code.startswith(("8", "4", "9")):
        return "北交所"
    return "其他"


def filter_by_board(
    codes: list[str],
    cfg: dict,
) -> list[str]:
    """根据配置过滤股票代码列表。

    cfg 期望字段：
      - board_filter
      - main_board_prefixes
      - exclude_prefixes
    """
    board = cfg.get("board_filter", "主板")
    main_prefixes = tuple(cfg.get("main_board_prefixes", ()))
    exclude_prefixes = tuple(cfg.get("exclude_prefixes", ()))

    if board == "全部 A 股":
        return [c for c in codes if not c.startswith(exclude_prefixes)]

    if board == "主板":
        return [c for c in codes if c.startswith(main_prefixes)]

    if board == "主板+创业板":
        keep = set(main_prefixes) | {"300", "301"}
        return [c for c in codes if c.startswith(tuple(keep))]

    raise ValueError(f"未知的 board_filter: {board!r}")
