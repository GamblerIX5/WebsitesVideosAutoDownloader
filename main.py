"""
WebsitesVideosAutoDownloader - 网站视频自动下载工具

统一入口：执行完整流水线（抓取 → 分类 → 下载）
"""

import argparse
import asyncio
import sys
from pathlib import Path

from core.pipeline import Pipeline
from config.settings import Config
from utils.logging_config import setup_logging


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="网站视频自动下载工具"
    )
    parser.add_argument("--config", "-c", type=str, help="配置文件路径")
    parser.add_argument(
        "--proxy", "-p",
        type=str,
        help="代理服务器地址（如 http://127.0.0.1:10808）"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="使用无头模式运行浏览器（默认：True）"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="不使用无头模式（显示浏览器窗口）"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="限制下载数量（用于测试）"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别"
    )
    parser.add_argument("--log-file", type=str, help="日志文件路径")
    return parser.parse_args()


def main() -> None:
    """主函数"""
    args = parse_args()

    log_file = args.log_file or "run.log"
    setup_logging(log_level=args.log_level, log_file=log_file)

    config = Config(args.config) if args.config else Config()

    if args.proxy:
        import os
        os.environ["HTTP_PROXY"] = args.proxy
        os.environ["HTTPS_PROXY"] = args.proxy

    headless = not args.no_headless
    pipeline = Pipeline(config)

    try:
        result = asyncio.run(pipeline.run(headless=headless))

        if result.news_count == 0:
            print("未抓取到任何新闻，请检查网络连接或代理设置")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n已终止")
        sys.exit(130)
    except Exception as e:
        print(f"执行失败：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
