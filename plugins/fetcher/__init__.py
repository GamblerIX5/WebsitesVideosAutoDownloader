"""抓取器插件模块"""

from .base import FetcherPlugin
from .mihoyo import MihoyoFetcher

__all__ = ["FetcherPlugin", "MihoyoFetcher"]
