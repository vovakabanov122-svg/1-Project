"""
Главное окно редактора
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
from datetime import datetime

from config import AppConfig, AppPaths
from core.editor import DocumentManager, TextAnalyzer
from core.auth import SessionManager
from .dialogs import *


class MainWindow:
    """Главное окно приложения"""

    def __init__(self, master, username, role, session_id):
        self.master = master
        self.username = username
        self.role = role
        self.session_id = session_id

        self.setup_window()
        self.init_managers()
        self.load_settings()
        self.create_menu()
        self.create_toolbar()
        self.create_main_area()
        self.create_statusbar()
        self.setup_bindings()

        # Показ приветственного сообщения
        self.show_welcome()

    def setup_window(self):
        """Настройка окна"""
        self.master.title(f"Текстовый редактор - {self.username} ({self.role})")
        self.master.geometry(f"{AppConfig.WINDOW_WIDTH}x{AppConfig.WINDOW_HEIGHT}")
        self.master.configure(bg='#f0f0f0')

        # Центрирование
        self.center_window()

    def center_window(self):
        """Центрирование окна"""
        self.master.update_idletasks()
        width = AppConfig.WINDOW_WIDTH
        height = AppConfig.WINDOW_HEIGHT
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f'{width}x{height}+{x}+{y}')

    def init_managers(self):
        """Инициализация менеджеров"""
        self.doc_manager = DocumentManager()
        self.text_analyzer = TextAnalyzer()
        self.session_manager = SessionManager()

        # Текущий документ
        self.current_file = None
        self.is_modified = False
        self.is_new = True

    def load_settings(self):
        """Загрузка настроек"""
        self.settings = AppConfig.load_settings()

        # Шрифт
        self.font_family = self.settings.get("font_family", "Arial")
        self.font_size = self.settings.get("font_size", 12)

    def create_menu(self):
        """Создание меню"""
        menubar = tk.Menu(self.master)

        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Новый", command=self.new_document, accelerator="Ctrl+N")
        file_menu.add_command(label="Открыть", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Сохранить", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Сохранить как...", command=self.save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Список документов", command=self.show_documents_list, accelerator="Ctrl+L")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_closing, accelerator="Alt+F4")
        menubar.add_cascade(label="Файл", menu=file_menu)

        # Меню Правка
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Найти", command=self.find_text, accelerator="Ctrl+F")
        edit_menu.add_command(label="Заменить", command=self.replace_text, accelerator="Ctrl+H")
        menubar.add_cascade(label="Правка", menu=edit_menu)

        # Меню Вид
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Увеличить шрифт", command=lambda: self.change_font_size(1))
        view_menu.add_command(label="Уменьшить шрифт", command=lambda: self.change_font_size(-1))
        menubar.add_cascade(label="Вид", menu=view_menu)

        # Меню Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.master.config(menu=menubar)

    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = tk.Frame(self.master, bg='#e0e0e0', height=40)
        toolbar.pack(fill=tk.X, padx=2, pady=2)

        # Кнопки
        buttons = [
            ("📄 Новый", self.new_document),
            ("📂 Открыть", self.open_file),
            ("💾 Сохранить", self.save_file),
            ("🔍 Найти", self.find_text),
            ("📊 Статистика", self.show_stats),
        ]

        for text, command in buttons:
            btn = tk.Button(toolbar, text=text,
                            command=command,
                            bg='#f5f5f5',
                            fg='#333333',
                            relief=tk.RAISED,
                            bd=1,
                            padx=12,
                            pady=5,
                            cursor="hand2")
            btn.pack(side=tk.LEFT, padx=2, pady=5)

    def create_main_area(self):
        """Создание основной области"""
        # Основной фрейм
        main_frame = tk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Текстовое поле с прокруткой
        text_frame = tk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Вертикальная прокрутка
        scroll_y = tk.Scrollbar(text_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Горизонтальная прокрутка
        scroll_x = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Текстовое поле
        self.text_widget = tk.Text(
            text_frame,
            wrap='word',
            undo=True,
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            font=(self.font_family, self.font_size),
            bg='white',
            fg='black',
            padx=10,
            pady=10
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        # Настройка прокруток
        scroll_y.config(command=self.text_widget.yview)
        scroll_x.config(command=self.text_widget.xview)

        # Привязка события изменения текста
        self.text_widget.bind('<KeyRelease>', self.on_text_changed)

    def create_statusbar(self):
        """Создание строки состояния"""
        self.statusbar = tk.Label(self.master,
                                  text="Готово | Документ: Не сохранен",
                                  bd=1,
                                  relief=tk.SUNKEN,
                                  anchor=tk.W,
                                  bg='#e0e0e0',
                                  fg='#333333')
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_bindings(self):
        """Настройка привязок клавиш"""
        self.master.bind('<Control-n>', lambda e: self.new_document())
        self.master.bind('<Control-o>', lambda e: self.open_file())
        self.master.bind('<Control-s>', lambda e: self.save_file())
        self.master.bind('<Control-l>', lambda e: self.show_documents_list())
        self.master.bind('<Control-f>', lambda e: self.find_text())
        self.master.bind('<Control-h>', lambda e: self.replace_text())

    def show_welcome(self):
        """Показ приветственного сообщения"""
        welcome_text = f"""Добро пожаловать, {self.username}!

Текстовый редактор Pro - профессиональный инструмент для работы с документами.

Ваша роль: {self.role}

Основные возможности:
• Создание и редактирование документов
• Поиск и замена текста
• Статистика документа
• Автоматическое сохранение

Для начала работы:
1. Создайте новый документ (Файл → Новый)
2. Или откройте существующий (Файл → Открыть)

Текущий документ: Не сохранен
"""
        self.text_widget.insert('1.0', welcome_text)
        self.update_status()

    def on_text_changed(self, event=None):
        """Обработчик изменения текста"""
        if self.is_new and self.text_widget.get('1.0', 'end-1c').strip():
            self.is_modified = True
            self.update_status()

    def update_status(self):
        """Обновление строки состояния"""
        if self.current_file:
            doc_name = os.path.basename(self.current_file)
            status = f"Документ: {doc_name}"
        else:
            status = "Документ: Не сохранен"

        if self.is_modified:
            status += " | Изменен"

        # Статистика текста
        text = self.text_widget.get('1.0', 'end-1c')
        lines = text.count('\n') + 1
        words = len(text.split())
        chars = len(text)

        status += f" | Строк: {lines} | Слов: {words} | Символов: {chars}"

        self.statusbar.config(text=status)
        self.master.title(f"Текстовый редактор - {status.split('|')[0]}")

    def new_document(self):
        """Создание нового документа"""
        if self.is_modified and self.text_widget.get('1.0', 'end-1c').strip():
            response = messagebox.askyesnocancel(
                "Новый документ",
                "Текущий документ изменен. Сохранить перед созданием нового?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_file()

        self.text_widget.delete('1.0', tk.END)
        self.current_file = None
        self.is_new = True
        self.is_modified = False
        self.update_status()

    def open_file(self):
        """Открытие файла"""
        filename = filedialog.askopenfilename(
            initialdir=str(AppPaths.DOCS_DIR),
            title="Выберите документ",
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("Все файлы", "*.*")
            ]
        )

        if filename:
            self.load_document_file(filename)

    def load_document_file(self, filename):
        """Загрузка документа из файла"""
        if self.is_modified and self.text_widget.get('1.0', 'end-1c').strip():
            response = messagebox.askyesnocancel(
                "Открыть файл",
                "Текущий документ изменен. Сохранить перед открытием нового?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_file()

        content = self.doc_manager.load_document(filename)
        if content is not None:
            self.text_widget.delete('1.0', tk.END)
            self.text_widget.insert('1.0', content)

            self.current_file = filename
            self.is_new = False
            self.is_modified = False

            # Добавляем в список недавних файлов
            self.add_to_recent_files(filename)

            self.update_status()

    def save_file(self):
        """Сохранение файла"""
        if not self.current_file or self.is_new:
            self.save_as()
        else:
            self.save_document()

    def save_as(self):
        """Сохранение как"""
        filename = filedialog.asksaveasfilename(
            initialdir=str(AppPaths.DOCS_DIR),
            title="Сохранить документ как",
            defaultextension=".txt",
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("Все файлы", "*.*")
            ]
        )

        if filename:
            if not filename.endswith('.txt'):
                filename += '.txt'

            self.save_document(filename)
            self.current_file = filename
            self.is_new = False
            self.is_modified = False

            # Добавляем в список недавних файлов
            self.add_to_recent_files(filename)

            self.update_status()

    def save_document(self, filename=None):
        """Сохранение документа"""
        if filename is None:
            filename = self.current_file

        content = self.text_widget.get('1.0', tk.END).strip()

        if self.doc_manager.save_document(filename, content):
            self.is_modified = False
            self.update_status()
            messagebox.showinfo("Сохранение", "Документ успешно сохранен")
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить документ")

    def add_to_recent_files(self, filename):
        """Добавление файла в список недавних"""
        if filename not in self.settings["recent_files"]:
            self.settings["recent_files"].insert(0, filename)
            # Ограничиваем размер списка
            if len(self.settings["recent_files"]) > 10:
                self.settings["recent_files"] = self.settings["recent_files"][:10]
            AppConfig.save_settings(self.settings)

    def show_documents_list(self):
        """Показать список документов"""
        show_documents_dialog(self.master, self.doc_manager, self.load_document_file)

    def find_text(self):
        """Поиск текста"""
        show_find_dialog(self.master, self.text_widget)

    def replace_text(self):
        """Замена текста"""
        show_replace_dialog(self.master, self.text_widget)

    def change_font_size(self, delta):
        """Изменение размера шрифта"""
        self.font_size = max(8, min(72, self.font_size + delta))
        self.text_widget.config(font=(self.font_family, self.font_size))

        # Сохраняем настройки
        self.settings["font_size"] = self.font_size
        AppConfig.save_settings(self.settings)

    def show_stats(self):
        """Показать статистику"""
        text = self.text_widget.get('1.0', 'end-1c')
        stats = self.text_analyzer.analyze_text(text)

        stats_text = f"""Статистика документа:

Основные показатели:
• Символов: {stats['characters']:,}
• Слов: {stats['words']:,}
• Строк: {stats['lines']:,}
• Пробелов: {stats['spaces']:,}
• Предложений: {stats['sentences']:,}

Средние значения:
• Длина слова: {stats['avg_word_length']:.1f} символов
• Длина строки: {stats['avg_line_length']:.1f} символов

Текущий документ: {os.path.basename(self.current_file) if self.current_file else 'Не сохранен'}
"""
        messagebox.showinfo("Статистика документа", stats_text)

    def show_about(self):
        """Показать информацию о программе"""
        about_text = f"""Текстовый редактор Pro v2.0

Профессиональный инструмент для работы с документами

Текущий пользователь: {self.username}
Роль: {self.role}

Разработчик: Ваша компания
Версия: 2.0
Лицензия: MIT

© 2024 Все права защищены
"""
        messagebox.showinfo("О программе", about_text)

    def on_closing(self):
        """Обработчик закрытия окна"""
        if self.is_modified and self.text_widget.get('1.0', 'end-1c').strip():
            response = messagebox.askyesnocancel(
                "Сохранение",
                "Документ был изменен. Сохранить изменения перед выходом?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_file()

        # Завершаем сессию
        self.session_manager.end_session(self.session_id)

        # Сохраняем настройки
        AppConfig.save_settings(self.settings)

        self.master.destroy()