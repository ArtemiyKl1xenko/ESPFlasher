"""
Theme Manager - управление темами оформления приложения (Dark/Light).
"""

import tkinter as tk
from typing import Dict, Tuple


# Темa Dark Mode
DARK_THEME = {
    'bg': '#1e1e1e',           # Фон окна
    'fg': '#e0e0e0',           # Текст
    'button_bg': '#353535',    # Фон кнопки
    'button_fg': '#ffffff',    # Текст кнопки
    'button_hover': '#454545', # Фон при наведении
    'input_bg': '#2d2d2d',     # Фон input полей
    'input_fg': '#e0e0e0',     # Текст input
    'frame_bg': '#252525',     # Фон фреймов
    'highlight': '#0078d4',    # Цвет выделения (синий)
    'success': '#107c10',      # Успешный статус (зеленый)
    'error': '#d13438',        # Ошибка (красный)
    'warning': '#ffb900',      # Предупреждение (оранжевый)
    'info': '#0078d4',         # Информация (синий)
    'border': '#3e3e42',       # Граница
}

# Тема Light Mode
LIGHT_THEME = {
    'bg': '#f5f5f5',           # Фон окна
    'fg': '#333333',           # Текст
    'button_bg': '#e1e1e1',    # Фон кнопки
    'button_fg': '#000000',    # Текст кнопки
    'button_hover': '#d4d4d4', # Фон при наведении
    'input_bg': '#ffffff',     # Фон input полей
    'input_fg': '#333333',     # Текст input
    'frame_bg': '#fafafa',     # Фон фреймов
    'highlight': '#0078d4',    # Цвет выделения
    'success': '#107c10',      # Успех
    'error': '#d13438',        # Ошибка
    'warning': '#ffb900',      # Предупреждение
    'info': '#0078d4',         # Информация
    'border': '#d0d0d0',       # Граница
}


class ThemeManager:
    """Менеджер тем оформления приложения."""

    def __init__(self, initial_theme: str = 'dark'):
        """
        Инициализация менеджера тем.

        Args:
            initial_theme: 'dark' или 'light'
        """
        self.current_theme = initial_theme
        self.theme_data = DARK_THEME if initial_theme == 'dark' else LIGHT_THEME
        self.callbacks = []  # Для уведомления об изменении темы

    def set_theme(self, theme_name: str) -> bool:
        """
        Установить новую тему.

        Args:
            theme_name: 'dark' или 'light'

        Returns:
            True если успешно установлено
        """
        if theme_name not in ('dark', 'light'):
            return False

        self.current_theme = theme_name
        self.theme_data = DARK_THEME if theme_name == 'dark' else LIGHT_THEME

        # Уведомляем всех слушателей
        for callback in self.callbacks:
            callback(theme_name)

        return True

    def on_theme_changed(self, callback):
        """
        Зарегистрировать callback при изменении темы.

        Args:
            callback: Функция, вызываемая с параметром (theme_name)
        """
        self.callbacks.append(callback)

    def get_color(self, color_key: str) -> str:
        """
        Получить цвет из текущей темы.

        Args:
            color_key: Название цвета (например: 'bg', 'fg', 'success')

        Returns:
            HEX код цвета
        """
        return self.theme_data.get(color_key, '#000000')

    def get_all_colors(self) -> Dict[str, str]:
        """Получить все цвета текущей темы."""
        return self.theme_data.copy()

    def apply_to_widget(self, widget: tk.Widget, style_type: str = 'normal'):
        """
        Применить тему к виджету.

        Args:
            widget: Tkinter виджет
            style_type: 'normal', 'button', 'input', 'frame'
        """
        try:
            if style_type == 'button':
                widget.config(
                    bg=self.get_color('button_bg'),
                    fg=self.get_color('button_fg'),
                    activebackground=self.get_color('button_hover'),
                    activeforeground=self.get_color('button_fg')
                )
            elif style_type == 'input':
                widget.config(
                    bg=self.get_color('input_bg'),
                    fg=self.get_color('input_fg'),
                    insertbackground=self.get_color('fg'),
                    selectbackground=self.get_color('highlight')
                )
            elif style_type == 'frame':
                widget.config(
                    bg=self.get_color('frame_bg')
                )
            else:  # normal
                widget.config(
                    bg=self.get_color('bg'),
                    fg=self.get_color('fg')
                )
        except tk.TclError:
            pass  # Виджет может не поддерживать эти настройки

    def get_theme_name(self) -> str:
        """Получить текущее названи темы."""
        return self.current_theme
