"""
Окно авторизации
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import getpass

from config import AppPaths, AppConfig
from core.auth import UserManager, LoginLogger, SessionManager


class LoginWindow(tk.Frame):
    """Окно входа в систему"""

    def __init__(self, master=None, on_login_success=None):
        super().__init__(master)
        self.master = master
        self.on_login_success = on_login_success

        self.setup_window()
        self.init_managers()
        self.load_settings()
        self.create_widgets()
        self.setup_bindings()

    def setup_window(self):
        """Настройка окна"""
        self.master.title("Текстовый редактор Pro - Вход в систему")
        self.master.geometry(f"{AppConfig.LOGIN_WIDTH}x{AppConfig.LOGIN_HEIGHT}")
        self.master.resizable(True, True)

        # Центрирование
        self.center_window()

        # Иконка
        self.setup_icon()

    def center_window(self):
        """Центрирование окна"""
        self.master.update_idletasks()
        width = AppConfig.LOGIN_WIDTH
        height = AppConfig.LOGIN_HEIGHT
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f'{width}x{height}+{x}+{y}')

    def setup_icon(self):
        """Настройка иконки"""
        # Здесь можно добавить загрузку иконки
        pass

    def init_managers(self):
        """Инициализация менеджеров"""
        self.user_manager = UserManager()
        self.logger = LoginLogger()
        self.session_manager = SessionManager()

        # Переменные состояния
        self.login_attempts = {}
        self.locked_out_until = {}

    def load_settings(self):
        """Загрузка настроек"""
        self.settings = AppConfig.load_settings()

        # Тема
        self.theme = self.settings.get("theme", "light")
        self.setup_theme()

    def setup_theme(self):
        """Настройка темы"""
        if self.theme == "dark":
            self.bg_color = '#1e1e1e'
            self.fg_color = '#ffffff'
            self.entry_bg = '#2d2d2d'
            self.button_bg = '#007acc'
            self.frame_bg = '#252526'
        else:
            self.bg_color = '#f5f5f5'
            self.fg_color = '#333333'
            self.entry_bg = '#ffffff'
            self.button_bg = '#4CAF50'
            self.frame_bg = '#ffffff'

    def create_widgets(self):
        """Создание виджетов"""
        # Основной контейнер
        main_container = tk.Frame(self.master, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Заголовок
        self.create_header(main_container)

        # Две колонки
        columns_frame = tk.Frame(main_container, bg=self.bg_color)
        columns_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Левая колонка - форма
        left_frame = tk.Frame(columns_frame, bg=self.bg_color)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Правая колонка - информация
        right_frame = tk.Frame(columns_frame, bg=self.bg_color, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

        # Создание формы входа
        self.create_login_form(left_frame)

        # Создание информационной панели
        self.create_info_panel(right_frame)

        # Футер
        self.create_footer(main_container)

    def create_header(self, parent):
        """Создание заголовка"""
        header_frame = tk.Frame(parent, bg=self.bg_color)
        header_frame.pack(pady=(0, 20))

        # Иконка
        icon_label = tk.Label(header_frame, text="📝",
                              font=("Arial", 56), bg=self.bg_color, fg='#007acc')
        icon_label.pack()

        # Название
        title_label = tk.Label(header_frame,
                               text="Текстовый редактор Pro",
                               font=("Arial", 28, "bold"),
                               bg=self.bg_color, fg=self.fg_color)
        title_label.pack()

        subtitle_label = tk.Label(header_frame,
                                  text="Профессиональный инструмент для работы с документами",
                                  font=("Arial", 12),
                                  bg=self.bg_color, fg='#666666')
        subtitle_label.pack()

    def create_login_form(self, parent):
        """Создание формы входа"""
        # Основной фрейм формы
        form_frame = tk.Frame(parent, bg=self.frame_bg,
                              relief=tk.RAISED, bd=2)
        form_frame.pack(fill=tk.BOTH, expand=True)

        inner_frame = tk.Frame(form_frame, bg=self.frame_bg, padx=25, pady=25)
        inner_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок формы
        tk.Label(inner_frame, text="Вход в систему",
                 font=("Arial", 18, "bold"),
                 bg=self.frame_bg, fg=self.fg_color).pack(pady=(0, 20))

        # Поле логина
        tk.Label(inner_frame, text="Имя пользователя",
                 font=("Arial", 11),
                 bg=self.frame_bg, fg=self.fg_color,
                 anchor='w').pack(fill=tk.X)

        self.username_var = tk.StringVar()
        username_entry = ttk.Combobox(
            inner_frame,
            textvariable=self.username_var,
            font=("Arial", 12),
            values=list(self.user_manager.users.keys()),
            state="normal"
        )
        username_entry.pack(fill=tk.X, pady=(5, 15))

        # Поле пароля
        tk.Label(inner_frame, text="Пароль",
                 font=("Arial", 11),
                 bg=self.frame_bg, fg=self.fg_color,
                 anchor='w').pack(fill=tk.X)

        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(
            inner_frame,
            textvariable=self.password_var,
            show="●",
            font=("Arial", 12)
        )
        self.password_entry.pack(fill=tk.X, pady=(5, 15))

        # Опции
        options_frame = tk.Frame(inner_frame, bg=self.frame_bg)
        options_frame.pack(fill=tk.X, pady=(0, 20))

        # Запомнить меня
        self.remember_var = tk.BooleanVar(value=False)
        remember_check = tk.Checkbutton(
            options_frame,
            text="Запомнить меня",
            variable=self.remember_var,
            bg=self.frame_bg,
            fg=self.fg_color,
            font=("Arial", 10)
        )
        remember_check.pack(side=tk.LEFT)

        # Кнопка входа
        self.login_button = tk.Button(
            inner_frame,
            text="Войти в систему",
            command=self.login,
            bg=self.button_bg,
            fg='white',
            font=("Arial", 12, "bold"),
            height=2,
            cursor="hand2"
        )
        self.login_button.pack(fill=tk.X, pady=(0, 10))

        # Статус
        self.status_label = tk.Label(
            inner_frame,
            text="",
            font=("Arial", 10),
            bg=self.frame_bg,
            fg=self.fg_color
        )
        self.status_label.pack(pady=(10, 0))

    def create_info_panel(self, parent):
        """Создание информационной панели"""
        info_frame = tk.Frame(parent, bg=self.frame_bg,
                              relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.BOTH, expand=True)

        inner_frame = tk.Frame(info_frame, bg=self.frame_bg, padx=20, pady=20)
        inner_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        tk.Label(inner_frame, text="Информация о системе",
                 font=("Arial", 14, "bold"),
                 bg=self.frame_bg, fg=self.fg_color).pack(pady=(0, 15))

        # Статистика
        stats = self.user_manager.get_user_count()
        total_users = sum(stats.values())

        tk.Label(inner_frame,
                 text=f"Всего пользователей: {total_users}",
                 font=("Arial", 11),
                 bg=self.frame_bg, fg=self.fg_color).pack(anchor='w', pady=2)

        for role, count in stats.items():
            tk.Label(inner_frame,
                     text=f"{role.capitalize()}: {count}",
                     font=("Arial", 11),
                     bg=self.frame_bg, fg=self.fg_color).pack(anchor='w', pady=2)

    def create_footer(self, parent):
        """Создание футера"""
        footer_frame = tk.Frame(parent, bg=self.bg_color)
        footer_frame.pack(fill=tk.X, pady=(20, 0))

        # Информация о системе
        system_info = tk.Label(
            footer_frame,
            text=f"Версия 2.0 | {getpass.getuser()} | {datetime.now().strftime('%H:%M')}",
            font=("Arial", 9),
            bg=self.bg_color,
            fg='#666666'
        )
        system_info.pack(side=tk.RIGHT)

    def setup_bindings(self):
        """Настройка привязок клавиш"""
        self.master.bind('<Return>', lambda e: self.login())
        self.master.bind('<Escape>', lambda e: self.master.destroy())

    def login(self):
        """Обработка входа"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        # Проверка блокировки
        if self.is_ip_locked():
            return

        # Валидация
        if not username or not password:
            self.show_status("Заполните все поля", "error")
            return

        # Аутентификация
        success, message, user_info = self.user_manager.authenticate(username, password)

        if success:
            # Логирование успеха
            self.logger.log_attempt(username, "SUCCESS")

            # Создание сессии
            session_id = self.session_manager.create_session(username, user_info)

            # Обновление статуса
            self.show_status("Успешный вход! Загружаем приложение...", "success")
            self.login_button.config(state='disabled', text="✓ Вход выполнен")

            # Запуск главного приложения
            self.master.after(1500, lambda: self.launch_editor(username,
                                                               user_info["role"],
                                                               session_id))
        else:
            # Логирование неудачи
            self.logger.log_attempt(username, "FAILURE")
            self.show_status(message, "error")
            self.record_failed_attempt()

    def is_ip_locked(self) -> bool:
        """Проверка блокировки по IP"""
        ip_address = getpass.getuser()  # В реальном приложении нужно получить реальный IP

        if ip_address in self.locked_out_until:
            lock_time = self.locked_out_until[ip_address]
            if datetime.now() < lock_time:
                remaining = (lock_time - datetime.now()).seconds
                minutes = remaining // 60
                seconds = remaining % 60

                self.show_status(
                    f"Слишком много попыток. Подождите {minutes} мин {seconds} сек.",
                    "error"
                )
                return True

        return False

    def record_failed_attempt(self):
        """Запись неудачной попытки"""
        ip_address = getpass.getuser()

        # Увеличиваем счетчик попыток
        if ip_address not in self.login_attempts:
            self.login_attempts[ip_address] = []

        self.login_attempts[ip_address].append(datetime.now())

        # Удаляем старые попытки
        cutoff_time = datetime.now().timestamp() - 3600  # Последний час
        self.login_attempts[ip_address] = [
            t for t in self.login_attempts[ip_address]
            if t.timestamp() > cutoff_time
        ]

        # Проверяем количество попыток
        if len(self.login_attempts[ip_address]) >= AppConfig.MAX_LOGIN_ATTEMPTS:
            lock_time = datetime.now().timestamp() + AppConfig.LOCKOUT_TIME
            self.locked_out_until[ip_address] = datetime.fromtimestamp(lock_time)
            self.show_status("Доступ заблокирован на 10 минут", "error")

    def show_status(self, message: str, status_type: str = "info"):
        """Отображение статуса"""
        colors = {
            "info": "#333333",
            "success": "#4CAF50",
            "error": "#f44336",
            "warning": "#FF9800"
        }

        self.status_label.config(text=message, fg=colors.get(status_type, "#333333"))

    def launch_editor(self, username: str, role: str, session_id: str):
        """Запуск редактора"""
        self.master.destroy()

        if self.on_login_success:
            self.on_login_success(username, role, session_id)
        else:
            # Запасной вариант
            from ui.main_window import MainWindow
            root = tk.Tk()
            app = MainWindow(root, username, role, session_id)
            root.mainloop()