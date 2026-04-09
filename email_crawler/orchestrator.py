"""Оркестрация процесса: поиск -> парсинг сайтов -> запись JSON."""

from __future__ import annotations

import asyncio
import logging

from playwright.async_api import async_playwright

from .config import CrawlConfig
from .search_parser import SearchParser
from .site_parser import SiteParser
from .storage import JsonRealtimeWriter


class CrawlOrchestrator:
    def __init__(self, config: CrawlConfig, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

    async def run(self) -> None:
        self.config.validate()
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.config.headless)
            context = await browser.new_context(ignore_https_errors=True)
            search_parser = SearchParser(
                context=context,
                logger=self.logger,
                timeout_ms=int(self.config.timeout_seconds * 1000),
            )
            site_parser = SiteParser(
                context=context,
                logger=self.logger,
                timeout_ms=int(self.config.timeout_seconds * 1000),
                retries=self.config.retries,
                retry_base_delay_seconds=self.config.retry_base_delay_seconds,
            )
            try:
                for city in self.config.cities:
                    await self._process_city(city, search_parser, site_parser)
            finally:
                await context.close()
                await browser.close()

    async def _process_city(self, city: str, search_parser: SearchParser, site_parser: SiteParser) -> None:
        writer = JsonRealtimeWriter(
            output_dir=self.config.output_dir,
            city=city,
            business_type=self.config.business_type,
            search_queries=self.config.search_queries,
            group_name=self.config.group_name if len(self.config.cities) > 1 else None,
        )
        self.logger.info("city_started | city=%s | business_type=%s", city, self.config.business_type)

        seen_sites: set[str] = set()
        seen_emails: set[str] = set()

        try:
            for query_base in self.config.search_queries:
                query = f"{query_base.strip()} {city}".strip()
                found_sites = await search_parser.search_sites(
                    query=query,
                    pages=self.config.search_pages,
                    delay_seconds=self.config.search_delay_seconds,
                )
                for _ in range(self.config.search_pages):
                    writer.increment_pages()

                for site_url in found_sites:
                    if len(seen_sites) >= self.config.max_sites_per_city:
                        break
                    if site_url in seen_sites:
                        continue

                    seen_sites.add(site_url)
                    writer.increment_sites()
                    self.logger.info("site_processing | city=%s | url=%s", city, site_url)

                    try:
                        extracted = await site_parser.extract_emails_from_site(
                            site_url=site_url,
                            site_delay_seconds=self.config.site_delay_seconds,
                        )
                        if not extracted:
                            continue

                        for email, found_at in extracted:
                            key = email.lower()
                            if key in seen_emails:
                                continue
                            seen_emails.add(key)
                            writer.add_email(email=email, source_url=site_url, found_at=found_at)
                            self.logger.info(
                                "email_found | city=%s | email=%s | source=%s | found_at=%s",
                                city,
                                email,
                                site_url,
                                found_at,
                            )
                    except Exception as exc:  # noqa: BLE001
                        writer.increment_errors()
                        self.logger.exception(
                            "site_parse_exception | city=%s | url=%s | error=%s",
                            city,
                            site_url,
                            exc,
                        )
                        continue
        except Exception as exc:  # noqa: BLE001
            writer.increment_errors()
            self.logger.exception("city_processing_exception | city=%s | error=%s", city, exc)
        finally:
            self.logger.info("city_finished | city=%s | output=%s", city, writer.path)
            await asyncio.sleep(0)
