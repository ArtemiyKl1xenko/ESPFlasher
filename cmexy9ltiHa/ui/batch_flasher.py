"""
Batch Flasher - мультиприватка нескольких устройств одновременно.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import List, Callable, Optional
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """Статусы задач."""
    PENDING = "Ожидание"
    IN_PROGRESS = "В процессе"
    COMPLETED = "Завершено"
    FAILED = "Ошибка"
    CANCELLED = "Отменено"


@dataclass
class BatchFlashTask:
    """Задача для batch флешинга."""
    device_port: str
    firmware_path: str
    task_id: str = ""
    baud_rate: int = 460800
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    message: str = ""
    start_time: datetime = None
    end_time: datetime = None
    duration_seconds: float = 0.0
    success: bool = False

    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"{self.device_port}_{int(datetime.now().timestamp())}"


class BatchFlasher:
    """Менеджер для batch флешинга нескольких устройств."""

    def __init__(self, max_concurrent: int = 4, on_status: Callable = None, on_progress: Callable = None):
        """
        Инициализация batch флешера.

        Args:
            max_concurrent: Максимальное количество одновременных операций
            on_status: Callback при изменении статуса задачи
            on_progress: Callback при изменении прогресса
        """
        self.max_concurrent = max_concurrent
        self.on_status = on_status or (lambda x: None)
        self.on_progress = on_progress or (lambda x: None)

        self.tasks: List[BatchFlashTask] = []
        self.queue: List[BatchFlashTask] = []
        self.active_threads: List[threading.Thread] = []
        self.is_running = False
        self.lock = threading.Lock()

    def add_task(self, device_port: str, firmware_path: str, baud_rate: int = 460800) -> str:
        """
        Добавить задачу в очередь.

        Args:
            device_port: COM порт устройства
            firmware_path: Путь к firmware файлу
            baud_rate: Скорость передачи

        Returns:
            ID задачи
        """
        task = BatchFlashTask(
            device_port=device_port,
            firmware_path=firmware_path,
            baud_rate=baud_rate
        )

        with self.lock:
            self.tasks.append(task)
            self.queue.append(task)

        self.on_status(f"[INFO] Задача добавлена: {device_port}\n")
        return task.task_id

    def start(self) -> bool:
        """
        Начать batch флеширование.

        Returns:
            True если успешно начато
        """
        if self.is_running:
            return False

        self.is_running = True

        # Создаем потоки обработчики
        for i in range(self.max_concurrent):
            thread = threading.Thread(
                target=self._worker_thread,
                name=f"FlasherWorker-{i}",
                daemon=True
            )
            thread.start()
            self.active_threads.append(thread)

        self.on_status(f"[✓ STARTED] Batch флешинг запущен ({self.max_concurrent} параллельно)\n")
        return True

    def stop(self):
        """Остановить batch флеширование."""
        self.is_running = False

        # Ждем завершения потоков
        for thread in self.active_threads:
            thread.join(timeout=5)

        self.active_threads.clear()
        self.on_status("[STOPPED] Batch флешинг остановлен\n")

    def _worker_thread(self):
        """Рабочий поток для обработки задач."""
        while self.is_running:
            task = None

            # Получаем задачу из очереди
            with self.lock:
                if self.queue:
                    task = self.queue.pop(0)

            if not task:
                time.sleep(0.1)
                continue

            # Выполняем задачу
            self._execute_task(task)

    def _execute_task(self, task: BatchFlashTask):
        """
        Выполнить задачу флешинга.

        Args:
            task: Задача для выполнения
        """
        task.status = TaskStatus.IN_PROGRESS
        task.start_time = datetime.now()
        self.on_status(f"[IN_PROGRESS] Начало прошивки {task.device_port}\n")

        try:
            # TODO: Реальная реализация флешинга через esptool
            # Здесь добавить вызов flasher_manager.flash()

            # Симуляция процесса
            for progress in range(0, 101, 10):
                task.progress = progress / 100.0
                self.on_progress((task.task_id, progress))
                time.sleep(0.5)

            task.status = TaskStatus.COMPLETED
            task.success = True
            task.message = "Успешно завершено"

            self.on_status(f"[✓ SUCCESS] {task.device_port} прошит успешно\n")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.message = str(e)
            self.on_status(f"[✗ ERROR] {task.device_port} - {str(e)}\n")

        finally:
            task.end_time = datetime.now()
            task.duration_seconds = (task.end_time - task.start_time).total_seconds()

    def get_task_status(self, task_id: str) -> Optional[BatchFlashTask]:
        """
        Получить статус задачи.

        Args:
            task_id: ID задачи

        Returns:
            BatchFlashTask объект или None
        """
        with self.lock:
            for task in self.tasks:
                if task.task_id == task_id:
                    return task
        return None

    def get_all_tasks(self) -> List[BatchFlashTask]:
        """Получить все задачи."""
        with self.lock:
            return self.tasks.copy()

    def get_statistics(self) -> dict:
        """
        Получить статистику выполнения.

        Returns:
            Словарь со статистикой
        """
        with self.lock:
            total = len(self.tasks)
            completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
            failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
            in_progress = sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS)

            return {
                'total': total,
                'completed': completed,
                'failed': failed,
                'in_progress': in_progress,
                'pending': total - completed - failed - in_progress,
                'success_rate': (completed / total * 100) if total > 0 else 0
            }
