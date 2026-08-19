"""
Custom Widgets - специализированные Tkinter компоненты.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable, Optional


class ScrollableFrame(ttk.Frame):
    """Фрейм с встроенной прокруткой."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Создаем Canvas и Scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        # Фрейм внутри Canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Паковка
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """Обработчик прокрутки мышью."""
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")


class ModernButton(tk.Button):
    """Кнопка с эффектами наведения."""

    def __init__(self, parent, theme_manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.theme_manager = theme_manager
        self.original_bg = kwargs.get('bg', '#353535')
        self.original_fg = kwargs.get('fg', '#ffffff')
        self.highlight_color = kwargs.get('activebackground', '#454545')

        # Биндим события наведения
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        """При наведении мыши."""
        self.config(bg=self.highlight_color)

    def _on_leave(self, event):
        """Когда мышь уходит."""
        self.config(bg=self.original_bg)


class StatusBar(ttk.Frame):
    """Статус бар для отображения статуса приложения."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Статус устройства
        self.device_status = ttk.Label(self, text="🔴 Нет подключения", relief=tk.SUNKEN)
        self.device_status.pack(side=tk.LEFT, padx=10, pady=5)

        # Разделитель
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Статус операции
        self.operation_status = ttk.Label(self, text="Готово", relief=tk.SUNKEN)
        self.operation_status.pack(side=tk.LEFT, padx=10, pady=5, expand=True, fill=tk.X)

        # Разделитель
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Версия
        self.version_label = ttk.Label(self, text="v5.0.0", relief=tk.SUNKEN)
        self.version_label.pack(side=tk.RIGHT, padx=10, pady=5)

    def set_device_status(self, status: str, connected: bool = False):
        """Установить статус устройства."""
        indicator = "🟢" if connected else "🔴"
        self.device_status.config(text=f"{indicator} {status}")

    def set_operation_status(self, status: str):
        """Установить статус операции."""
        self.operation_status.config(text=status)

    def set_version(self, version: str):
        """Установить версию."""
        self.version_label.config(text=f"v{version}")


class LogViewer(tk.Frame):
    """Видёр для просмотра логов с поддержкой фильтрации и поиска."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Кнопка очистки
        ttk.Button(toolbar, text="Очистить", command=self.clear_logs).pack(side=tk.LEFT, padx=2)

        # Кнопка экспорта
        ttk.Button(toolbar, text="Экспорт", command=self.export_logs).pack(side=tk.LEFT, padx=2)

        # Checkbox для auto-scroll
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(toolbar, text="Auto Scroll", variable=self.auto_scroll_var).pack(side=tk.LEFT, padx=10)

        # Поле поиска
        ttk.Label(toolbar, text="🔍 Поиск:").pack(side=tk.LEFT, padx=(20, 2))
        self.search_entry = ttk.Entry(toolbar, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Найти", command=self.search_logs).pack(side=tk.LEFT, padx=2)

        # Text widget для логов
        self.text = scrolledtext.ScrolledText(
            self,
            height=15,
            width=80,
            font=('Courier New', 9),
            state=tk.DISABLED
        )
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tags для цветирования
        self.text.tag_config('error', foreground='#d13438')
        self.text.tag_config('warning', foreground='#ffb900')
        self.text.tag_config('success', foreground='#107c10')
        self.text.tag_config('info', foreground='#0078d4')
        self.text.tag_config('debug', foreground='#888888')

    def add_log(self, message: str, level: str = 'info'):
        """
        Добавить сообщение в лог.

        Args:
            message: Текст сообщения
            level: Уровень ('error', 'warning', 'success', 'info', 'debug')
        """
        self.text.config(state=tk.NORMAL)

        # Вставляем текст
        self.text.insert(tk.END, message, level)

        # Auto-scroll если включен
        if self.auto_scroll_var.get():
            self.text.see(tk.END)

        self.text.config(state=tk.DISABLED)

    def clear_logs(self):
        """Очистить все логи."""
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.config(state=tk.DISABLED)

    def search_logs(self):
        """Найти текст в логах."""
        search_text = self.search_entry.get()
        if not search_text:
            return

        # Очищаем предыдущие результаты
        self.text.tag_remove('highlight', '1.0', tk.END)

        # Ищем
        idx = '1.0'
        while True:
            idx = self.text.search(search_text, idx, nocase=True, stopindex=tk.END)
            if not idx:
                break
            end_idx = f"{idx}+{len(search_text)}c"
            self.text.tag_add('highlight', idx, end_idx)
            idx = end_idx

        self.text.tag_config('highlight', background='yellow', foreground='black')

    def export_logs(self):
        """Экспортировать логи в файл (заглушка)."""
        content = self.text.get(1.0, tk.END)
        # TODO: Реализовать сохранение в файл
        print(f"[INFO] Экспорт {len(content)} символов")
