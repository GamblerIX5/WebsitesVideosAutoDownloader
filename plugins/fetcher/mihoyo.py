"""
米哈游官网抓取器
"""

import logging
from typing import List, Optional

from playwright.async_api import async_playwright, ProxySettings

from core.models import NewsItem
from plugins.fetcher.base import FetcherPlugin
from core.plugin import PluginMetadata, PluginRegistry
from urllib.parse import urljoin

logger = logging.getLogger("fetcher.mihoyo")

NEWS_ITEM_SELECTOR = '.news-list .list-wrap > a[href*="/news/"]'
LOAD_MORE_BUTTON_SELECTOR = ".btn-more-wrap"


class MihoyoFetcher(FetcherPlugin):
    """米哈游官网新闻抓取器"""

    metadata = PluginMetadata(
        name="mihoyo",
        version="1.0.0",
        description="米哈游官网新闻抓取器",
    )

    async def fetch_news(self, headless: bool = True, **kwargs) -> List[NewsItem]:
        """
        从米哈游官网抓取新闻列表

        Args:
            headless: 是否使用无头模式

        Returns:
            新闻条目列表
        """
        news_url = urljoin(self.base_url, "/news?nav=news")
        proxy_config: Optional[ProxySettings] = None

        if self.proxy:
            proxy_config = ProxySettings(server=self.proxy)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless,
                args=["--disable-blink-features=AutomationControlled"],
            )

            try:
                context = await browser.new_context(proxy=proxy_config)
                page = await context.new_page()

                logger.info("正在访问新闻列表：%s", news_url)
                await page.goto(news_url, wait_until="domcontentloaded")

                try:
                    await page.wait_for_selector(
                        NEWS_ITEM_SELECTOR, timeout=15000
                    )
                except Exception:
                    logger.error("超时未加载出任何新闻")
                    return []

                initial_count = await page.locator(NEWS_ITEM_SELECTOR).count()
                logger.info("初始加载了 %d 条新闻", initial_count)

                # 检查"加载更多"按钮是否存在
                load_more_btn = page.locator(LOAD_MORE_BUTTON_SELECTOR).first
                btn_exists = await load_more_btn.count() > 0
                logger.info("'加载更多' 按钮存在：%s", btn_exists)

                if btn_exists:
                    click_count = 0
                    while True:
                        try:
                            if not await load_more_btn.is_visible():
                                logger.info("'加载更多' 按钮不可见，停止点击")
                                break

                            click_count += 1
                            logger.info("第 %d 次点击'加载更多'...", click_count)
                            await load_more_btn.click()
                            await page.wait_for_timeout(1500)

                            # 检查是否有新内容加载
                            new_count = await page.locator(NEWS_ITEM_SELECTOR).count()
                            logger.info("当前新闻数：%d", new_count)

                        except Exception as e:
                            logger.info("点击过程出现异常：%s，停止点击", str(e))
                            break

                    logger.info("共点击了 %d 次'加载更多'", click_count)
                else:
                    logger.warning("未找到'加载更多' 按钮，可能是网页结构变更")

                items = await page.evaluate(
                    """(selector) => {
                        const elements = document.querySelectorAll(selector);
                        const results = [];
                        for (const el of elements) {
                            const href = el.getAttribute('href');
                            if (!href) continue;

                            const titleNode = el.querySelector('.title');
                            let title = '';
                            if (titleNode) {
                                title = titleNode.innerText.trim();
                            } else {
                                const text = el.innerText || '';
                                const lines = text.split('\\n')
                                    .map(l => l.trim())
                                    .filter(Boolean);
                                title = lines[0] || '';
                            }

                            if (title) {
                                results.push({ title, href });
                            }
                        }
                        return results;
                    }""",
                    NEWS_ITEM_SELECTOR,
                )

                news_items = [
                    NewsItem(
                        title=item["title"],
                        url=urljoin(self.base_url, item["href"]),
                    )
                    for item in items
                    if item.get("title")
                ]

                logger.info("共抓取 %d 条新闻", len(news_items))
                return news_items

            finally:
                await browser.close()


PluginRegistry.register("mihoyo", MihoyoFetcher)
