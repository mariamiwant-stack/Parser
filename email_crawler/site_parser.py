"""Извлечение email с сайтов предприятий."""

from __future__ import annotations

import asyncio
import logging
import re
from urllib.parse import urljoin, urlparse

from playwright.async_api import BrowserContext

from .constants import CAPTCHA_MARKERS, COMMON_CONTACT_PATHS, DEFAULT_DISPOSABLE_DOMAIN_BLACKLIST

EMAIL_RE = re.compile(r"[\w.\-+%]+@[\w.\-]+\.[a-z]{2,}", re.IGNORECASE)


class SiteParser:
    def __init__(
        self,
        context: BrowserContext,
        logger: logging.Logger,
        timeout_ms: int,
        retries: int,
        retry_base_delay_seconds: float,
        blocked_domains: set[str] | None = None,
    ) -> None:
        self.context = context
        self.logger = logger
        self.timeout_ms = timeout_ms
        self.retries = retries
        self.retry_base_delay_seconds = retry_base_delay_seconds
        self.blocked_domains = blocked_domains or DEFAULT_DISPOSABLE_DOMAIN_BLACKLIST

    async def extract_emails_from_site(self, site_url: str, site_delay_seconds: float) -> list[tuple[str, str]]:
        """Ищет email на главной и контактных страницах.

        Возвращает пары (email, found_at).
        """
        candidates = self._build_candidate_urls(site_url)
        found: list[tuple[str, str]] = []

        for candidate_url, found_at in candidates:
            html = await self._fetch_with_retry(candidate_url)
            await asyncio.sleep(site_delay_seconds)
            if html is None:
                continue
            if self._contains_captcha(html):
                self.logger.warning("captcha_detected | stage=site | url=%s", candidate_url)
                continue

            for email in self._extract_emails(html):
                found.append((email, found_at))

        # Сохраняем порядок, удаляем дубль email внутри сайта.
        seen: set[str] = set()
        unique: list[tuple[str, str]] = []
        for email, found_at in found:
            key = email.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append((email, found_at))
        return unique

    def _build_candidate_urls(self, site_url: str) -> list[tuple[str, str]]:
        parsed = urlparse(site_url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        candidates: list[tuple[str, str]] = []
        for path in COMMON_CONTACT_PATHS:
            if path:
                candidates.append((urljoin(root, path), "contacts"))
            else:
                candidates.append((root, "homepage"))
        return candidates

    async def _fetch_with_retry(self, url: str) -> str | None:
        for attempt in range(1, self.retries + 1):
            page = await self.context.new_page()
            try:
                response = await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )
                if response is None:
                    raise RuntimeError("empty_response")
                if response.status >= 400:
                    raise RuntimeError(f"http_status_{response.status}")
                html = await page.content()
                return html
            except Exception as exc:  # noqa: BLE001
                delay = self.retry_base_delay_seconds * (2 ** (attempt - 1))
                self.logger.warning(
                    "site_fetch_error | url=%s | attempt=%s/%s | error=%s | retry_in=%.2fs",
                    url,
                    attempt,
                    self.retries,
                    exc,
                    delay,
                )
                if attempt < self.retries:
                    await asyncio.sleep(delay)
                else:
                    self.logger.exception("site_fetch_failed | url=%s | final_error=%s", url, exc)
            finally:
                await page.close()
        return None

    def _extract_emails(self, html: str) -> list[str]:
        matches = EMAIL_RE.findall(html)
        valid: list[str] = []
        for raw in matches:
            email = raw.strip(" <>\"'()[]{}.,;:")
            domain = email.split("@")[-1].lower()
            if domain in self.blocked_domains:
                continue
            valid.append(email)
        return valid

    @staticmethod
    def _contains_captcha(html_text: str) -> bool:
        low = html_text.lower()
        return any(marker in low for marker in CAPTCHA_MARKERS)
