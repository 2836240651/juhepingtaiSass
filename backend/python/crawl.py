#!/usr/bin/env python3
"""入口：python crawl.py [--date YYYY-MM-DD] [--seed]"""
from __future__ import annotations

import argparse
import sys

from app.ingest import run_ingest


def main() -> None:
    parser = argparse.ArgumentParser(description="Temu 爬虫入库")
    parser.add_argument("--date", help="上报日期 YYYY-MM-DD，默认今天")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="使用 demo 种子数据（不打开浏览器）",
    )
    args = parser.parse_args()

    try:
        result = run_ingest(args.date, use_seed=args.seed)
    except Exception as exc:
        print(f"爬取失败: {exc}", file=sys.stderr)
        print("提示: 首次请先 py login.py 登录；或临时用 py crawl.py --seed", file=sys.stderr)
        sys.exit(1)

    print(
        f"report_time={result['report_time']} shops={result['shops']} rows={result['rows']}"
    )


if __name__ == "__main__":
    main()
