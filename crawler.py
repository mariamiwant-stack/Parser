"""CLI-утилита для парсинга email адресов предприятий по городам РФ.

Пример:
python crawler.py \
  --business-type "автосервисы" \
  --queries "автосервисы,автосервисы лучшие" \
  --city "Москва" \
  --pages 3 --max-sites 40 --search-delay 2 --site-delay 1.5
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from email_crawler.config import CrawlConfig
from email_crawler.constants import TOP_16_RU_CITIES
from email_crawler.logging_utils import setup_logger
from email_crawler.orchestrator import CrawlOrchestrator


def _parse_city_selection(args: argparse.Namespace) -> list[str]:
    if args.all_cities:
        return TOP_16_RU_CITIES.copy()
    if args.cities:
        return [item.strip() for item in args.cities.split(",") if item.strip()]
    if args.city:
        return [args.city.strip()]
    raise ValueError("Укажите --city, --cities или --all-cities")


def _parse_queries(raw_queries: str) -> list[str]:
    queries = [item.strip() for item in raw_queries.split(",") if item.strip()]
    if not queries:
        raise ValueError("Нужна минимум одна поисковая фраза в --queries")
    return queries


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Надежный парсер email адресов предприятий (Python + Playwright)",
    )
    parser.add_argument("--business-type", required=True, help="Тип бизнеса: автосервисы, стоматологии и т.д.")
    parser.add_argument(
        "--queries",
        required=True,
        help="Поисковые фразы через запятую, например: 'автосервисы,автосервисы лучшие'",
    )

    city_group = parser.add_mutually_exclusive_group(required=True)
    city_group.add_argument("--city", help="Один город, например: Москва")
    city_group.add_argument("--cities", help="Список городов через запятую")
    city_group.add_argument("--all-cities", action="store_true", help="Использовать топ-16 городов России")

    parser.add_argument("--group-name", default="group_1", help="Идентификатор группы для имени файла")
    parser.add_argument("--pages", type=int, default=3, help="Количество страниц выдачи на запрос (1..10)")
    parser.add_argument("--max-sites", type=int, default=50, help="Лимит сайтов на город")
    parser.add_argument("--search-delay", type=float, default=1.5, help="Задержка между запросами к поиску, сек")
    parser.add_argument("--site-delay", type=float, default=1.0, help="Задержка между запросами к сайтам, сек")
    parser.add_argument("--timeout", type=float, default=20.0, help="Таймаут страницы, сек")
    parser.add_argument("--retries", type=int, default=3, help="Число ретраев для недоступных сайтов")
    parser.add_argument(
        "--retry-base-delay",
        type=float,
        default=1.0,
        help="Базовая задержка для экспоненциального retry, сек",
    )
    parser.add_argument("--headful", action="store_true", help="Выключить headless и запустить видимый браузер")
    parser.add_argument("--output-dir", default="output", help="Каталог JSON результатов")
    parser.add_argument("--log-file", default="logs/crawler.log", help="Файл логов")
    return parser


async def _main_async(args: argparse.Namespace) -> None:
    cities = _parse_city_selection(args)
    queries = _parse_queries(args.queries)

    config = CrawlConfig(
        business_type=args.business_type,
        search_queries=queries,
        cities=cities,
        search_pages=args.pages,
        max_sites_per_city=args.max_sites,
        search_delay_seconds=args.search_delay,
        site_delay_seconds=args.site_delay,
        timeout_seconds=args.timeout,
        retries=args.retries,
        retry_base_delay_seconds=args.retry_base_delay,
        headless=not args.headful,
        output_dir=Path(args.output_dir),
        log_path=Path(args.log_file),
        group_name=args.group_name,
    )

    logger = setup_logger(config.log_path)
    logger.info(
        "crawler_started | business_type=%s | cities=%s | queries=%s",
        config.business_type,
        config.cities,
        config.search_queries,
    )

    orchestrator = CrawlOrchestrator(config=config, logger=logger)
    await orchestrator.run()
    logger.info("crawler_finished")


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()
