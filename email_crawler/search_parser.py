"""Поиск сайтов предприятий через Playwright."""

from __future__ import annotations

import asyncio
import logging
from urllib.parse import quote_plus

from playwright.async_api import BrowserContext

from .constants import CAPTCHA_MARKERS


class SearchParser:
    def __init__(self, context: BrowserContext, logger: logging.Logger, timeout_ms: int) -> None:
        self.context = context
        self.logger = logger
        self.timeout_ms = timeout_ms

    async def search_sites(
        self,
        query: str,
        pages: int,
        delay_seconds: float,
    ) -> list[str]:
        """Возвращает список URL из выдачи DuckDuckGo (html версия)."""
        links: list[str] = []
        page = await self.context.new_page()

        try:
            for page_num in range(pages):
                start = page_num * 30
                search_url = (
                    "https://duckduckgo.com/html/?q="
                    f"{quote_plus(query)}&s={start}"
                )
                try:
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                    html = (await page.content()).lower()
                    if self._contains_captcha(html):
                        self.logger.warning(
                            "captcha_detected | stage=search | query=%s | page=%s",
                            query,
                            page_num + 1,
                        )
                        continue

                    anchors = await page.query_selector_all("a.result__a")
                    for anchor in anchors:
                        href = await anchor.get_attribute("href")
                        if href and href.startswith("http"):
                            links.append(href)
                    await asyncio.sleep(delay_seconds)
                except Exception as exc:  # noqa: BLE001
                    self.logger.exception(
                        "search_page_error | query=%s | page=%s | error=%s",
                        query,
                        page_num + 1,
                        exc,
                    )
                    continue
        finally:
            await page.close()

        return list(dict.fromkeys(links))

    @staticmethod
    def _contains_captcha(html_text: str) -> bool:
        return any(marker in html_text for marker in CAPTCHA_MARKERS)
