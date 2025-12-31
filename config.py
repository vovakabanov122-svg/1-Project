"""
Конфигурация приложения
"""
import os
import json
from pathlib import Path

class AppConfig:
    """Класс конфигурации приложения"""

    # Пути к папкам
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    DOCS_DIR = BASE_DIR / "docs"
    REPORTS_DIR = BASE_DIR / "reports"
    BACKUPS_DIR = BASE_DIR / "backups"

    # Файлы
    SETTINGS_FILE = DATA_DIR / "login_settings.json"
    USERS_FILE = DATA_DIR / "users.json"
    LOG_FILE = DATA_DIR / "login_log.csv"
    APP_SETTINGS_FILE = DATA_DIR / "app_settings.json"
    REPORTS_INDEX = REPORTS_DIR / "_reports_index.json"

    @classmethod
    def init_directories(cls):
        """Создание всех необходимых директорий"""
        directories = [cls.DATA_DIR, cls.DOCS_DIR,
                      cls.REPORTS_DIR, cls.BACKUPS_DIR]
        for directory in directories:
            directory.mkdir(exist_ok=True)
        return cls

# Инициализация директорий при импорте
config = AppConfig.init_directories()