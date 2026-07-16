"""用 headless Chrome 截 GitHub 仓库主页（README 渲染区）。"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = "https://github.com/kingchen24/cn-info-disclosure-tracker"
OUT = OUT_DIR / "github-repo.png"


def shoot(url: str, out: Path, width: int = 1280, height: int = 1800,
          full_page: bool = True, wait_ms: int = 2500):
    cmd = [
        CHROME,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        f"--window-size={width},{height}",
        f"--screenshot={out}",
        "--virtual-time-budget=10000",
        url,
    ]
    subprocess.run(cmd, check=True)
    print(f"[OK] {out}  ({out.stat().st_size} bytes)")


def main():
    # README 区
    shoot(URL, OUT_DIR / "github-repo.png", width=1280, height=1800)
    # 移动端（更聚焦）
    shoot(URL, OUT_DIR / "github-repo-narrow.png", width=900, height=1500)


if __name__ == "__main__":
    main()
