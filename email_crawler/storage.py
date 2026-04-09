"""Слой сохранения результатов в JSON с немедленной записью."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from .constants import CITY_SLUGS


@dataclass(slots=True)
class CrawlStats:
    total_pages: int = 0
    total_sites_parsed: int = 0
    total_emails_found: int = 0
    errors: int = 0


class JsonRealtimeWriter:
    """Пишет результаты в JSON при каждом изменении состояния."""

    def __init__(
        self,
        output_dir: Path,
        city: str,
        business_type: str,
        search_queries: list[str],
        group_name: str | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.city = city
        self.business_type = business_type
        self.search_queries = search_queries
        self.stats = CrawlStats()
        self.data = self._build_initial_payload()
        self.path = self._resolve_path(group_name)
        self._load_existing_if_present()
        self.flush()

    def _resolve_path(self, group_name: str | None) -> Path:
        business_slug = self.business_type.lower().strip().replace(" ", "_")
        if group_name:
            base_name = f"emails_{group_name}_{business_slug}"
        else:
            city_slug = CITY_SLUGS.get(self.city, self.city.lower().replace(" ", "_"))
            base_name = f"emails_{city_slug}_{business_slug}"

        candidate = self.output_dir / f"{base_name}.json"
        if not candidate.exists():
            return candidate

        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
        return self.output_dir / f"{base_name}_{timestamp}.json"

    def _build_initial_payload(self) -> dict[str, Any]:
        return {
            "city": self.city,
            "business_type": self.business_type,
            "search_queries": self.search_queries,
            "emails": [],
            "stats": {
                "total_pages": 0,
                "total_sites_parsed": 0,
                "total_emails_found": 0,
                "errors": 0,
            },
        }

    def _load_existing_if_present(self) -> None:
        # Если выбран новый файл по timestamp — данных нет.
        if not self.path.exists():
            return
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            self.data = self._build_initial_payload()

    def increment_pages(self) -> None:
        self.data["stats"]["total_pages"] += 1
        self.flush()

    def increment_sites(self) -> None:
        self.data["stats"]["total_sites_parsed"] += 1
        self.flush()

    def increment_errors(self) -> None:
        self.data["stats"]["errors"] += 1
        self.flush()

    def add_email(self, email: str, source_url: str, found_at: str) -> None:
        self.data["emails"].append(
            {
                "email": email,
                "source_url": source_url,
                "found_at": found_at,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        self.data["stats"]["total_emails_found"] = len(self.data["emails"])
        self.flush()

    def flush(self) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(self.path)
