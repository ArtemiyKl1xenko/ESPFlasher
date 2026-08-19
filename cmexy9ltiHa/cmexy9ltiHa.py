import sys
import os
import threading
import subprocess
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# Add current directory to path for relative imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    import serial
    import serial.tools.list_ports
except Exception:
    serial = None

from models import FileEntry, FlashProfile, FlashOperation
from config_manager import ConfigManager
from flasher_manager import FlasherManager
from esp_utils import ESPChipDetector, get_flash_params_for_chip


class ESPFlasherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ESP32 Flasher — полное управление прошивкой")
        self.geometry("1200x700")

        # Initialize managers
        self.config_manager = ConfigManager()
        self.flasher_manager = FlasherManager(on_log=self.append_log)

        # UI state
        self.create_widgets()
        self.monitor_thread = None
        self.monitor_stop = threading.Event()
        self.ser = None
        self.flash_start_time = None

        # Load last config on startup
        self.load_last_config()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        """Create main UI with tabs."""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Flash
        self.flash_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.flash_tab, text="📝 Прошивка")
        self.create_flash_tab()

        # Tab 2: Monitor
        self.monitor_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.monitor_tab, text="📊 Монитор")
        self.create_monitor_tab()

        # Tab 3: Profiles
        self.profiles_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.profiles_tab, text="💾 Профили")
        self.create_profiles_tab()

        # Tab 4: History
        self.history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.history_tab, text="📜 История")
        self.create_history_tab()

    def create_flash_tab(self):
        """Create Flash tab UI."""
        frm = self.flash_tab

        # Connection frame
        conn = ttk.LabelFrame(frm, text="Подключение")
        conn.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(conn, text="Порт:").grid(row=0, column=0, sticky=tk.W, padx=4, pady=4)
        self.port_combo = ttk.Combobox(conn, values=self.list_ports(), width=15)
        self.port_combo.grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(conn, text="Скорость:").grid(row=0, column=2, sticky=tk.W, padx=4, pady=4)
        self.baud_entry = ttk.Combobox(conn, values=[115200, 230400, 460800, 921600], width=10)
        self.baud_entry.set(460800)
        self.baud_entry.grid(row=0, column=3, padx=4, pady=4)

        self.refresh_button = ttk.Button(conn, text="🔄 Обновить", command=self.refresh_ports)
        self.refresh_button.grid(row=0, column=4, padx=4, pady=4)

        self.detect_button = ttk.Button(conn, text="🔍 Определить", command=self.detect_chip)
        self.detect_button.grid(row=0, column=5, padx=4, pady=4)

        ttk.Label(conn, text="Чип:").grid(row=0, column=6, sticky=tk.W, padx=4, pady=4)
        self.chip_combo = ttk.Combobox(conn, values=ESPChipDetector.get_all_chip_names(), width=12)
        self.chip_combo.set("ESP32")
        self.chip_combo.grid(row=0, column=7, padx=4, pady=4)

        self.auto_detect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(conn, text="Автопараметры", variable=self.auto_detect_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=4)

        # Files table frame
        files_fr = ttk.LabelFrame(frm, text="Файлы для прошивки")
        files_fr.pack(fill=tk.BOTH, expand=True, pady=8)

        # TreeView for files with columns
        tree_frame = ttk.Frame(files_fr)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        scroll = ttk.Scrollbar(tree_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.files_tree = ttk.Treeview(tree_frame, columns=("address", "path"), height=8, yscrollcommand=scroll.set)
        scroll.config(command=self.files_tree.yview)

        self.files_tree.column("#0", width=0, stretch=False)
        self.files_tree.column("address", anchor=tk.W, width=100)
        self.files_tree.column("path", anchor=tk.W, width=400)

        self.files_tree.heading("#0", text="", anchor=tk.W)
        self.files_tree.heading("address", text="Адрес (hex)", anchor=tk.W)
        self.files_tree.heading("path", text="Путь к файлу", anchor=tk.W)

        self.files_tree.pack(fill=tk.BOTH, expand=True)

        # File management buttons
        btn_frame = ttk.Frame(files_fr)
        btn_frame.pack(fill=tk.X, padx=4, pady=4)

        ttk.Button(btn_frame, text="➕ Добавить файл", command=self.add_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✏️ Редактировать", command=self.edit_file_entry).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="❌ Удалить", command=self.remove_file_entry).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ Очистить", command=self.clear_files).pack(side=tk.LEFT, padx=2)

        # Address input for quick add
        addr_frame = ttk.Frame(files_fr)
        addr_frame.pack(fill=tk.X, padx=4, pady=4)

        ttk.Label(addr_frame, text="Адрес для новых файлов:").pack(side=tk.LEFT, padx=2)
        self.addr_entry = ttk.Entry(addr_frame, width=12)
        self.addr_entry.insert(0, "0x1000")
        self.addr_entry.pack(side=tk.LEFT, padx=2)

        ttk.Button(addr_frame, text="➕ Добавить с адресом", command=self.add_file_with_addr).pack(side=tk.LEFT, padx=2)

        # Action buttons
        act_fr = ttk.Frame(frm)
        act_fr.pack(fill=tk.X, pady=8)

        self.erase_button = ttk.Button(act_fr, text="🗑️ Стереть Flash", command=self.erase_flash)
        self.erase_button.pack(side=tk.LEFT, padx=4, pady=4)

        self.flash_button = ttk.Button(act_fr, text="⚡ Прошить", command=self.start_flash)
        self.flash_button.pack(side=tk.LEFT, padx=4, pady=4)

        self.stop_flash_button = ttk.Button(act_fr, text="⏹️ Остановить", command=self.stop_flash, state=tk.DISABLED)
        self.stop_flash_button.pack(side=tk.LEFT, padx=4, pady=4)

        # Log
        log_fr = ttk.LabelFrame(frm, text="Лог")
        log_fr.pack(fill=tk.BOTH, expand=True, pady=8)

        self.log_text = tk.Text(log_fr, wrap=tk.NONE, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        log_btns = ttk.Frame(frm)
        log_btns.pack(fill=tk.X)
        ttk.Button(log_btns, text="🗑️ Очистить лог", command=lambda: self.log_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=4, pady=4)

    def create_monitor_tab(self):
        """Create Monitor tab UI."""
        frm = self.monitor_tab

        # Monitor controls
        mon_fr = ttk.LabelFrame(frm, text="Параметры монитора")
        mon_fr.pack(fill=tk.X, pady=8)

        ttk.Label(mon_fr, text="Скорость (baud):").grid(row=0, column=0, sticky=tk.W, padx=4, pady=4)
        self.monitor_baud = ttk.Combobox(mon_fr, values=[74880, 115200, 230400, 460800], width=10)
        self.monitor_baud.set(115200)
        self.monitor_baud.grid(row=0, column=1, padx=4, pady=4)

        self.start_mon_btn = ttk.Button(mon_fr, text="▶️ Запустить", command=self.start_monitor)
        self.start_mon_btn.grid(row=0, column=2, padx=4, pady=4)

        self.stop_mon_btn = ttk.Button(mon_fr, text="⏹️ Остановить", command=self.stop_monitor, state=tk.DISABLED)
        self.stop_mon_btn.grid(row=0, column=3, padx=4, pady=4)

        # Monitor output
        mon_out = ttk.LabelFrame(frm, text="Вывод монитора")
        mon_out.pack(fill=tk.BOTH, expand=True, pady=8)

        self.monitor_text = tk.Text(mon_out, wrap=tk.WORD)
        self.monitor_text.pack(fill=tk.BOTH, expand=True)

        # Clear button
        ttk.Button(frm, text="🗑️ Очистить", command=lambda: self.monitor_text.delete(1.0, tk.END)).pack(fill=tk.X, padx=4, pady=4)

    def create_profiles_tab(self):
        """Create Profiles tab UI."""
        frm = self.profiles_tab

        # Profile list
        list_fr = ttk.LabelFrame(frm, text="Сохраненные профили")
        list_fr.pack(fill=tk.BOTH, expand=True, pady=8)

        self.profiles_listbox = tk.Listbox(list_fr, height=12)
        self.profiles_listbox.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.profiles_listbox.bind('<<ListboxSelect>>', lambda e: self.on_profile_select())
        self.refresh_profiles_list()

        # Profile management buttons
        btn_fr = ttk.Frame(frm)
        btn_fr.pack(fill=tk.X, pady=8)

        ttk.Button(btn_fr, text="💾 Сохранить текущую как профиль", command=self.save_current_as_profile).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_fr, text="📂 Загрузить профиль", command=self.load_selected_profile).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_fr, text="✏️ Переименовать", command=self.rename_profile).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_fr, text="❌ Удалить профиль", command=self.delete_profile).pack(side=tk.LEFT, padx=4)

        # Import/Export
        imp_exp_fr = ttk.Frame(frm)
        imp_exp_fr.pack(fill=tk.X, pady=8)

        ttk.Button(imp_exp_fr, text="📤 Экспортировать", command=self.export_profile_dialog).pack(side=tk.LEFT, padx=4)
        ttk.Button(imp_exp_fr, text="📥 Импортировать", command=self.import_profile_dialog).pack(side=tk.LEFT, padx=4)

    def create_history_tab(self):
        """Create History tab UI."""
        frm = self.history_tab

        # History table
        hist_fr = ttk.LabelFrame(frm, text="История операций прошивки")
        hist_fr.pack(fill=tk.BOTH, expand=True, pady=8)

        scroll = ttk.Scrollbar(hist_fr)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_tree = ttk.Treeview(hist_fr, columns=("profile", "port", "files", "success", "time", "duration"), 
                                        yscrollcommand=scroll.set)
        scroll.config(command=self.history_tree.yview)

        self.history_tree.column("#0", width=0, stretch=False)
        self.history_tree.column("profile", anchor=tk.W, width=100)
        self.history_tree.column("port", anchor=tk.W, width=80)
        self.history_tree.column("files", anchor=tk.CENTER, width=50)
        self.history_tree.column("success", anchor=tk.CENTER, width=80)
        self.history_tree.column("time", anchor=tk.W, width=140)
        self.history_tree.column("duration", anchor=tk.CENTER, width=80)

        self.history_tree.heading("#0", text="", anchor=tk.W)
        self.history_tree.heading("profile", text="Профиль", anchor=tk.W)
        self.history_tree.heading("port", text="Порт", anchor=tk.W)
        self.history_tree.heading("files", text="Файлов", anchor=tk.CENTER)
        self.history_tree.heading("success", text="Статус", anchor=tk.CENTER)
        self.history_tree.heading("time", text="Время", anchor=tk.W)
        self.history_tree.heading("duration", text="Длит. (сек)", anchor=tk.CENTER)

        self.history_tree.pack(fill=tk.BOTH, expand=True)

        self.refresh_history_view()

        # Clear button
        ttk.Button(frm, text="🗑️ Очистить историю", command=self.clear_history).pack(fill=tk.X, padx=4, pady=4)

    # ============ PORT MANAGEMENT ============

    def list_ports(self):
        if serial is None:
            return []
        ports = [p.device for p in serial.tools.list_ports.comports()]
        return ports

    def refresh_ports(self):
        self.port_combo['values'] = self.list_ports()

    # ============ FILE MANAGEMENT ============

    def add_file(self):
        """Add file(s) with current address."""
        paths = filedialog.askopenfilenames(filetypes=[("BIN files", "*.bin"), ("All files", "*")])
        addr = self.addr_entry.get().strip()

        if not addr.startswith('0x'):
            messagebox.showerror("Ошибка", "Адрес должен быть в hex формате, например 0x1000")
            return

        for p in paths:
            self.files_tree.insert('', tk.END, values=(addr, p))

    def add_file_with_addr(self):
        """Add file with specified address."""
        paths = filedialog.askopenfilenames(filetypes=[("BIN files", "*.bin"), ("All files", "*")])
        addr = self.addr_entry.get().strip()

        if not addr.startswith('0x'):
            messagebox.showerror("Ошибка", "Адрес должен быть в hex формате, например 0x1000")
            return

        for p in paths:
            self.files_tree.insert('', tk.END, values=(addr, p))

    def edit_file_entry(self):
        """Edit selected file entry."""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите файл для редактирования")
            return

        item = selection[0]
        values = self.files_tree.item(item, 'values')

        # Create edit dialog
        dialog = tk.Toplevel(self)
        dialog.title("Редактировать запись")
        dialog.geometry("400x150")
        dialog.resizable(False, False)

        ttk.Label(dialog, text="Адрес (hex):").grid(row=0, column=0, padx=4, pady=4, sticky=tk.W)
        addr_entry = ttk.Entry(dialog, width=30)
        addr_entry.insert(0, values[0])
        addr_entry.grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(dialog, text="Путь:").grid(row=1, column=0, padx=4, pady=4, sticky=tk.W)
        path_entry = ttk.Entry(dialog, width=30)
        path_entry.insert(0, values[1])
        path_entry.grid(row=1, column=1, padx=4, pady=4)

        def save_changes():
            addr = addr_entry.get().strip()
            path = path_entry.get().strip()

            if not addr.startswith('0x'):
                messagebox.showerror("Ошибка", "Адрес должен быть в hex формате")
                return

            if not path:
                messagebox.showerror("Ошибка", "Путь не может быть пустым")
                return

            self.files_tree.item(item, values=(addr, path))
            dialog.destroy()

        ttk.Button(dialog, text="Сохранить", command=save_changes).grid(row=2, column=0, columnspan=2, padx=4, pady=10)

    def remove_file_entry(self):
        """Remove selected file entry."""
        selection = self.files_tree.selection()
        for item in selection:
            self.files_tree.delete(item)

    def clear_files(self):
        """Clear all file entries."""
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

    def get_files_from_tree(self) -> list:
        """Get FileEntry objects from tree."""
        files = []
        for item in self.files_tree.get_children():
            values = self.files_tree.item(item, 'values')
            files.append(FileEntry(address=values[0], path=values[1]))
        return files

    # ============ CHIP DETECTION ============

    def detect_chip(self):
        port = self.port_combo.get().strip()
        if not port:
            messagebox.showerror("Ошибка", "Выберите порт сначала")
            return

        self.detect_button.config(state=tk.DISABLED)

        def detect_in_thread():
            try:
                self.flasher_manager.detect_chip(port, int(self.baud_entry.get()))
            finally:
                self.after(0, lambda: self.detect_button.config(state=tk.NORMAL))

        thread = threading.Thread(target=detect_in_thread, daemon=True)
        thread.start()

    # ============ FLASH OPERATIONS ============

    def start_flash(self):
        port = self.port_combo.get().strip()
        if not port:
            messagebox.showerror("Ошибка", "Выберите порт")
            return

        files = self.get_files_from_tree()
        if not files:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один файл для прошивки")
            return

        self.flash_button.config(state=tk.DISABLED)
        self.stop_flash_button.config(state=tk.NORMAL)
        self.flash_start_time = datetime.now()

        baud = int(self.baud_entry.get())
        auto_detect = self.auto_detect_var.get()

        # Get selected chip
        chip = None
        if hasattr(self, 'chip_combo'):
            chip_name = self.chip_combo.get()
            if chip_name:
                chip = ESPChipDetector.get_chip_by_name(chip_name)

        def flash_in_thread():
            try:
                success = self.flasher_manager.flash(port, baud, files, auto_detect, chip=chip)

                # Record operation in history
                duration = (datetime.now() - self.flash_start_time).total_seconds()
                operation = FlashOperation(
                    profile_name="Manual Flash",
                    port=port,
                    baud_rate=baud,
                    files_count=len(files),
                    success=success,
                    duration_seconds=duration
                )
                self.config_manager.add_operation_to_history(operation)
                self.refresh_history_view()

            finally:
                self.after(0, self.flash_finished)

        thread = threading.Thread(target=flash_in_thread, daemon=True)
        thread.start()

    def flash_finished(self):
        self.flash_button.config(state=tk.NORMAL)
        self.stop_flash_button.config(state=tk.DISABLED)

    def stop_flash(self):
        self.flasher_manager.stop()
        self.append_log("\n[WARNING] Прошивка остановлена пользователем\n")

    # ============ ERASE OPERATIONS ============

    def erase_flash(self):
        port = self.port_combo.get().strip()
        if not port:
            messagebox.showerror("Ошибка", "Выберите порт")
            return

        if messagebox.askyesno("Подтверждение", "Вы уверены? Это сотрет всю Flash память!"):
            self.erase_button.config(state=tk.DISABLED)

            def erase_in_thread():
                try:
                    self.flasher_manager.erase_flash(port, int(self.baud_entry.get()))
                finally:
                    self.after(0, lambda: self.erase_button.config(state=tk.NORMAL))

            thread = threading.Thread(target=erase_in_thread, daemon=True)
            thread.start()

    # ============ LOGGING ============

    def append_log(self, text):
        """Append text to log (thread-safe)."""
        def _append():
            self.log_text.insert(tk.END, text)
            self.log_text.see(tk.END)
        self.after(0, _append)

    # ============ SERIAL MONITOR ============

    def start_monitor(self):
        if serial is None:
            messagebox.showerror("Ошибка", "Модуль pyserial не установлен")
            return

        port = self.port_combo.get().strip()
        if not port:
            messagebox.showerror("Ошибка", "Выберите порт")
            return

        baud = int(self.monitor_baud.get())

        try:
            self.ser = serial.Serial(port, baud, timeout=0.2)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return

        self.monitor_stop.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        self.start_mon_btn.config(state=tk.DISABLED)
        self.stop_mon_btn.config(state=tk.NORMAL)
        self.monitor_text.insert(tk.END, f"[Monitor] Открыт {port} @ {baud}\n")

    def _monitor_loop(self):
        try:
            while not self.monitor_stop.is_set():
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting)
                    try:
                        s = data.decode('utf-8', errors='replace')
                    except Exception:
                        s = str(data)

                    def add_to_monitor():
                        self.monitor_text.insert(tk.END, s)
                        self.monitor_text.see(tk.END)

                    self.after(0, add_to_monitor)
                time.sleep(0.05)
        except Exception as e:
            self.after(0, lambda: self.monitor_text.insert(tk.END, f"[Monitor error] {e}\n"))
        finally:
            try:
                self.ser.close()
            except Exception:
                pass

            def finish():
                self.monitor_text.insert(tk.END, "[Monitor] Остановлен\n")
                self.start_mon_btn.config(state=tk.NORMAL)
                self.stop_mon_btn.config(state=tk.DISABLED)

            self.after(0, finish)

    def stop_monitor(self):
        self.monitor_stop.set()

    # ============ PROFILE MANAGEMENT ============

    def refresh_profiles_list(self):
        """Refresh profiles list."""
        self.profiles_listbox.delete(0, tk.END)
        profiles = self.config_manager.get_all_profiles()
        for profile in profiles:
            self.profiles_listbox.insert(tk.END, profile.name)

    def on_profile_select(self):
        """Handle profile selection."""
        selection = self.profiles_listbox.curselection()
        if selection:
            profile_name = self.profiles_listbox.get(selection[0])
            profile = self.config_manager.get_profile(profile_name)
            if profile:
                self.load_profile_to_ui(profile)

    def load_profile_to_ui(self, profile: FlashProfile):
        """Load profile data into UI."""
        self.port_combo.set(profile.port or "")
        self.baud_entry.set(str(profile.baud_rate))
        self.auto_detect_var.set(profile.auto_detect)

        # Clear and load files
        self.clear_files()
        for file_entry in profile.files:
            self.files_tree.insert('', tk.END, values=(file_entry.address, file_entry.path))

    def save_current_as_profile(self):
        """Save current configuration as a profile."""
        dialog = tk.Toplevel(self)
        dialog.title("Сохранить профиль")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Имя профиля:").grid(row=0, column=0, padx=4, pady=4, sticky=tk.W)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(dialog, text="Описание:").grid(row=1, column=0, padx=4, pady=4, sticky=tk.NW)
        desc_text = tk.Text(dialog, height=4, width=30)
        desc_text.grid(row=1, column=1, padx=4, pady=4)

        def save_profile():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Внимание", "Введите имя профиля")
                return

            if self.config_manager.profile_exists(name):
                if not messagebox.askyesno("Подтверждение", f"Профиль '{name}' уже существует. Перезаписать?"):
                    return

            files = self.get_files_from_tree()
            description = desc_text.get(1.0, tk.END).strip()

            profile = FlashProfile(
                name=name,
                description=description,
                files=files,
                baud_rate=int(self.baud_entry.get()),
                port=self.port_combo.get().strip(),
                auto_detect=self.auto_detect_var.get()
            )

            self.config_manager.save_profile(profile)
            self.refresh_profiles_list()
            messagebox.showinfo("Успешно", f"Профиль '{name}' сохранен")
            dialog.destroy()

        ttk.Button(dialog, text="Сохранить", command=save_profile).grid(row=2, column=0, columnspan=2, padx=4, pady=10)

    def load_selected_profile(self):
        """Load selected profile."""
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите профиль для загрузки")
            return

        profile_name = self.profiles_listbox.get(selection[0])
        profile = self.config_manager.get_profile(profile_name)
        if profile:
            self.load_profile_to_ui(profile)
            messagebox.showinfo("Успешно", f"Профиль '{profile_name}' загружен")

    def rename_profile(self):
        """Rename selected profile."""
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите профиль для переименования")
            return

        old_name = self.profiles_listbox.get(selection[0])
        profile = self.config_manager.get_profile(old_name)
        if not profile:
            return

        dialog = tk.Toplevel(self)
        dialog.title("Переименовать профиль")
        dialog.geometry("300x100")
        dialog.resizable(False, False)

        ttk.Label(dialog, text="Новое имя:").grid(row=0, column=0, padx=4, pady=4)
        name_entry = ttk.Entry(dialog, width=20)
        name_entry.insert(0, old_name)
        name_entry.grid(row=0, column=1, padx=4, pady=4)

        def rename():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("Внимание", "Введите новое имя")
                return

            if new_name != old_name and self.config_manager.profile_exists(new_name):
                messagebox.showerror("Ошибка", f"Профиль '{new_name}' уже существует")
                return

            profile.name = new_name
            self.config_manager.save_profile(profile)
            self.config_manager.delete_profile(old_name)
            self.refresh_profiles_list()
            messagebox.showinfo("Успешно", f"Профиль переименован на '{new_name}'")
            dialog.destroy()

        ttk.Button(dialog, text="Переименовать", command=rename).grid(row=1, column=0, columnspan=2, padx=4, pady=10)

    def delete_profile(self):
        """Delete selected profile."""
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите профиль для удаления")
            return

        profile_name = self.profiles_listbox.get(selection[0])

        if messagebox.askyesno("Подтверждение", f"Удалить профиль '{profile_name}'?"):
            self.config_manager.delete_profile(profile_name)
            self.refresh_profiles_list()
            messagebox.showinfo("Успешно", f"Профиль '{profile_name}' удален")

    def export_profile_dialog(self):
        """Export selected profile to file."""
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите профиль для экспорта")
            return

        profile_name = self.profiles_listbox.get(selection[0])
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*")],
            initialfile=f"{profile_name}.json"
        )

        if filepath:
            if self.config_manager.export_profile(profile_name, filepath):
                messagebox.showinfo("Успешно", f"Профиль экспортирован в {filepath}")
            else:
                messagebox.showerror("Ошибка", "Не удалось экспортировать профиль")

    def import_profile_dialog(self):
        """Import profile from file."""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*")]
        )

        if filepath:
            profile = self.config_manager.import_profile(filepath)
            if profile:
                self.refresh_profiles_list()
                messagebox.showinfo("Успешно", f"Профиль '{profile.name}' импортирован")
            else:
                messagebox.showerror("Ошибка", "Не удалось импортировать профиль")

   # ============ HISTORY MANAGEMENT ============

    def refresh_history_view(self):
        """Refresh history view."""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        operations = self.config_manager.get_history(limit=50)
        for op in operations:
            status = "✓ Успешно" if op.success else "✗ Ошибка"
            
            try:
                timestamp_dt = datetime.fromisoformat(op.timestamp)
            except Exception:
                from datetime import datetime
                timestamp_dt = datetime.now()
                
            time_str = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")

            self.history_tree.insert('', tk.END, values=(
                op.profile_name,
                op.port,
                op.files_count,
                status,
                time_str,
                f"{op.duration_seconds:.1f}"
            ))

    def clear_history(self):
        """Clear all history."""
        if messagebox.askyesno("Подтверждение", "Очистить всю историю операций?"):
            self.config_manager.clear_history()
            self.refresh_history_view()
            messagebox.showinfo("Успешно", "История очищена")


    # ============ CONFIGURATION PERSISTENCE ============

    def load_last_config(self):
        """Load last configuration on startup."""
        config = self.config_manager.load_last_config()
        if config:
            try:
                if 'port' in config:
                    self.port_combo.set(config.get('port', ''))
                if 'baud' in config:
                    self.baud_entry.set(str(config.get('baud', 460800)))
                if 'auto_detect' in config:
                    self.auto_detect_var.set(config.get('auto_detect', True))
                if 'files' in config:
                    for file_data in config['files']:
                        self.files_tree.insert('', tk.END, values=(file_data['address'], file_data['path']))
                if 'monitor_baud' in config:
                    self.monitor_baud.set(str(config.get('monitor_baud', 115200)))
            except Exception as e:
                print(f"Error loading last config: {e}")

    def save_current_config(self):
        """Save current configuration."""
        config = {
            'port': self.port_combo.get(),
            'baud': int(self.baud_entry.get()),
            'auto_detect': self.auto_detect_var.get(),
            'monitor_baud': int(self.monitor_baud.get()),
            'files': [{'address': values[0], 'path': values[1]} 
                     for values in [self.files_tree.item(item, 'values') 
                                   for item in self.files_tree.get_children()]]
        }
        self.config_manager.save_last_config(config)

    def on_close(self):
        """Save configuration and close app."""
        self.save_current_config()
        self.quit()


if __name__ == '__main__':
    app = ESPFlasherApp()
    app.mainloop()
