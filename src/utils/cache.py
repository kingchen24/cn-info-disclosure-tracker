"""磁盘 JSON 缓存工具：按 (key, params) 存储返回值。

设计目标：
- 抓取脚本可随时中断；下次启动自动复用已抓数据
- 抓取失败的 key 用 ``__error__`` 标记，方便排错
- 单文件 <name>.json，结构 {key: payload}
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class JsonCache:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.data = {}
        else:
            self.data = {}

    def get(self, key: str) -> Any | None:
        return self.data.get(key)

    def has(self, key: str) -> bool:
        return key in self.data

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def __len__(self) -> int:
        return len(self.data)


def retry(callable_, *args, attempts: int = 3, sleep: float = 0.6, **kwargs) -> Any:
    """轻量重试封装：失败时指数退避，返回最后一次异常。"""
    last = None
    for i in range(attempts):
        try:
            return callable_(*args, **kwargs)
        except Exception as e:  # noqa: BLE001 - 顶层吞所有异常
            last = e
            time.sleep(sleep * (i + 1))
    raise last  # type: ignore[misc]
