"""Конфигурационные модели и парсинг параметров CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class CrawlConfig:
    business_type: str
    search_queries: list[str]
    cities: list[str]
    search_pages: int = 3
    max_sites_per_city: int = 50
    search_delay_seconds: float = 1.5
    site_delay_seconds: float = 1.0
    timeout_seconds: float = 20.0
    retries: int = 3
    retry_base_delay_seconds: float = 1.0
    headless: bool = True
    output_dir: Path = Path("output")
    log_path: Path = Path("logs/crawler.log")
    group_name: str | None = None

    def validate(self) -> None:
        """Проверяет ограничения параметров, чтобы избежать невалидного запуска."""
        if not self.business_type.strip():
            raise ValueError("business_type не может быть пустым")
        if not self.search_queries:
            raise ValueError("Нужна хотя бы одна поисковая фраза")
        if not self.cities:
            raise ValueError("Нужен хотя бы один город")
        if not (1 <= self.search_pages <= 10):
            raise ValueError("search_pages должно быть в диапазоне 1..10")
        if self.max_sites_per_city <= 0:
            raise ValueError("max_sites_per_city должно быть > 0")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds должно быть > 0")
        if self.retries < 1:
            raise ValueError("retries должно быть >= 1")
        if self.search_delay_seconds < 0 or self.site_delay_seconds < 0:
            raise ValueError("Задержки не могут быть отрицательными")
