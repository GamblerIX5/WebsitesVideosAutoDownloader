"""
抓取器插件基类
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any

from core.plugin import Plugin
from core.models import NewsItem


class FetcherPlugin(Plugin, ABC):
    """抓取器插件基类"""

    def __init__(self, base_url: str, proxy: Optional[str] = None, **kwargs: Any):
        self.base_url = base_url
        self.proxy = proxy

    @abstractmethod
    async def fetch_news(self, **kwargs: Any) -> List[NewsItem]:
        """
        抓取新闻列表

        Returns:
            新闻条目列表
        """
        pass

    async def execute(self, data: Optional[Any] = None, **kwargs: Any) -> List[NewsItem]:
        """执行抓取"""
        return await self.fetch_news(**kwargs)
