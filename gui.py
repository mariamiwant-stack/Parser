"""Простой GUI для Windows (Tkinter) поверх crawler логики."""

from __future__ import annotations

import asyncio
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

from email_crawler.config import CrawlConfig
from email_crawler.constants import TOP_16_RU_CITIES
from email_crawler.logging_utils import setup_logger
from email_crawler.orchestrator import CrawlOrchestrator


class CrawlerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Business Email Crawler (Windows GUI)")
        self.root.geometry("980x700")

        self.business_type_var = tk.StringVar(value="автосервисы")
        self.queries_var = tk.StringVar(value="автосервисы,автосервисы лучшие")
        self.city_mode_var = tk.StringVar(value="single")
        self.city_var = tk.StringVar(value=TOP_16_RU_CITIES[0])
        self.cities_var = tk.StringVar(value="Москва,Санкт-Петербург")
        self.group_name_var = tk.StringVar(value="group_1")

        self.pages_var = tk.IntVar(value=3)
        self.max_sites_var = tk.IntVar(value=50)
        self.search_delay_var = tk.DoubleVar(value=1.5)
        self.site_delay_var = tk.DoubleVar(value=1.0)
        self.timeout_var = tk.DoubleVar(value=20.0)
        self.retries_var = tk.IntVar(value=3)
        self.retry_base_delay_var = tk.DoubleVar(value=1.0)
        self.headless_var = tk.BooleanVar(value=True)

        self.output_dir_var = tk.StringVar(value="output")
        self.log_file_var = tk.StringVar(value="logs/crawler.log")

        self._is_running = False

        self._build_ui()

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        form = ttk.LabelFrame(main, text="Параметры", padding=10)
        form.pack(fill=tk.X)

        self._add_row(form, 0, "Тип бизнеса", ttk.Entry(form, textvariable=self.business_type_var, width=60))
        self._add_row(form, 1, "Поисковые фразы (через запятую)", ttk.Entry(form, textvariable=self.queries_var, width=60))

        mode_frame = ttk.Frame(form)
        ttk.Radiobutton(mode_frame, text="Один город", variable=self.city_mode_var, value="single").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Группа городов", variable=self.city_mode_var, value="group").pack(side=tk.LEFT, padx=8)
        ttk.Radiobutton(mode_frame, text="Все 16 городов", variable=self.city_mode_var, value="all").pack(side=tk.LEFT)
        self._add_row(form, 2, "Режим городов", mode_frame)

        self._add_row(form, 3, "Город (single)", ttk.Combobox(form, textvariable=self.city_var, values=TOP_16_RU_CITIES, width=57))
        self._add_row(form, 4, "Города (group, через запятую)", ttk.Entry(form, textvariable=self.cities_var, width=60))
        self._add_row(form, 5, "Имя группы", ttk.Entry(form, textvariable=self.group_name_var, width=60))

        perf = ttk.LabelFrame(main, text="Настройки производительности", padding=10)
        perf.pack(fill=tk.X, pady=(10, 0))

        self._add_row(perf, 0, "Страниц выдачи (1..10)", ttk.Spinbox(perf, from_=1, to=10, textvariable=self.pages_var, width=10))
        self._add_row(perf, 1, "Макс. сайтов на город", ttk.Spinbox(perf, from_=1, to=1000, textvariable=self.max_sites_var, width=10))
        self._add_row(perf, 2, "Задержка поиска (сек)", ttk.Entry(perf, textvariable=self.search_delay_var, width=10))
        self._add_row(perf, 3, "Задержка сайтов (сек)", ttk.Entry(perf, textvariable=self.site_delay_var, width=10))
        self._add_row(perf, 4, "Timeout (сек)", ttk.Entry(perf, textvariable=self.timeout_var, width=10))
        self._add_row(perf, 5, "Retry attempts", ttk.Spinbox(perf, from_=1, to=10, textvariable=self.retries_var, width=10))
        self._add_row(perf, 6, "Retry base delay (сек)", ttk.Entry(perf, textvariable=self.retry_base_delay_var, width=10))
        ttk.Checkbutton(perf, text="Headless mode", variable=self.headless_var).grid(row=7, column=1, sticky="w", pady=4)

        path_box = ttk.LabelFrame(main, text="Пути", padding=10)
        path_box.pack(fill=tk.X, pady=(10, 0))
        self._add_row(path_box, 0, "Каталог результатов", ttk.Entry(path_box, textvariable=self.output_dir_var, width=60))
        self._add_row(path_box, 1, "Файл логов", ttk.Entry(path_box, textvariable=self.log_file_var, width=60))

        controls = ttk.Frame(main)
        controls.pack(fill=tk.X, pady=(10, 0))
        self.start_btn = ttk.Button(controls, text="Запуск", command=self.start)
        self.start_btn.pack(side=tk.LEFT)

        self.status_label = ttk.Label(controls, text="Готово")
        self.status_label.pack(side=tk.LEFT, padx=15)

        log_frame = ttk.LabelFrame(main, text="Живой лог", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.log_widget = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=16)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

    @staticmethod
    def _add_row(parent: ttk.Frame, row: int, label: str, widget: tk.Widget) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        widget.grid(row=row, column=1, sticky="w", pady=4)

    def _append_log(self, text: str) -> None:
        self.log_widget.insert(tk.END, f"{text}\n")
        self.log_widget.see(tk.END)
        self.status_label.config(text=text)

    def _status_callback(self, text: str) -> None:
        self.root.after(0, lambda: self._append_log(text))

    def start(self) -> None:
        if self._is_running:
            messagebox.showinfo("Информация", "Процесс уже запущен")
            return

        try:
            config = self._build_config()
            config.validate()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Ошибка параметров", str(exc))
            return

        self._is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self._append_log("Запуск краулера...")

        thread = threading.Thread(target=self._run_background, args=(config,), daemon=True)
        thread.start()

    def _build_config(self) -> CrawlConfig:
        queries = [q.strip() for q in self.queries_var.get().split(",") if q.strip()]

        mode = self.city_mode_var.get()
        if mode == "single":
            cities = [self.city_var.get().strip()]
        elif mode == "group":
            cities = [c.strip() for c in self.cities_var.get().split(",") if c.strip()]
        else:
            cities = TOP_16_RU_CITIES.copy()

        group_name = self.group_name_var.get().strip() if len(cities) > 1 else None

        return CrawlConfig(
            business_type=self.business_type_var.get().strip(),
            search_queries=queries,
            cities=cities,
            search_pages=self.pages_var.get(),
            max_sites_per_city=self.max_sites_var.get(),
            search_delay_seconds=self.search_delay_var.get(),
            site_delay_seconds=self.site_delay_var.get(),
            timeout_seconds=self.timeout_var.get(),
            retries=self.retries_var.get(),
            retry_base_delay_seconds=self.retry_base_delay_var.get(),
            headless=self.headless_var.get(),
            output_dir=Path(self.output_dir_var.get().strip()),
            log_path=Path(self.log_file_var.get().strip()),
            group_name=group_name,
        )

    def _run_background(self, config: CrawlConfig) -> None:
        logger = setup_logger(config.log_path)
        logger.info("gui_run_started")
        try:
            orchestrator = CrawlOrchestrator(config=config, logger=logger, status_callback=self._status_callback)
            asyncio.run(orchestrator.run())
            self.root.after(0, lambda: self._append_log("Готово: процесс завершён"))
        except Exception as exc:  # noqa: BLE001
            logger.exception("gui_run_failed | error=%s", exc)
            self.root.after(0, lambda: messagebox.showerror("Ошибка", str(exc)))
        finally:
            logger.info("gui_run_finished")
            self.root.after(0, self._unlock)

    def _unlock(self) -> None:
        self._is_running = False
        self.start_btn.config(state=tk.NORMAL)


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    app = CrawlerGUI(root)
    app._append_log("Интерфейс готов. Заполните параметры и нажмите 'Запуск'.")
    root.mainloop()


if __name__ == "__main__":
    main()
