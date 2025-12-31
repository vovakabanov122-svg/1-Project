"""
Модуль аутентификации и управления пользователями
"""
import json
import hashlib
import secrets
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from config import AppPaths, AppConfig


class PasswordHasher:
    """Класс для безопасного хеширования паролей"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширование пароля с уникальной солью"""
        # Генерация уникальной соли для каждого пользователя
        salt = secrets.token_bytes(32).hex()
        # Используем PBKDF2 для замедления атак
        iterations = 100000
        dk = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        )
        # Сохраняем соль и хеш
        return f"{salt}${iterations}${dk.hex()}"

    @staticmethod
    def verify_password(hashed_password: str, provided_password: str) -> bool:
        """Проверка пароля"""
        try:
            salt, iterations, stored_hash = hashed_password.split('$')
            iterations = int(iterations)
            dk = hashlib.pbkdf2_hmac(
                'sha256',
                provided_password.encode('utf-8'),
                salt.encode('utf-8'),
                iterations
            )
            return dk.hex() == stored_hash
        except:
            return False

    @staticmethod
    def validate_password_complexity(password: str) -> Tuple[bool, str]:
        """Проверка сложности пароля"""
        if len(password) < AppConfig.PASSWORD_MIN_LENGTH:
            return False, f"Пароль должен быть не менее {AppConfig.PASSWORD_MIN_LENGTH} символов"

        if not any(c.isdigit() for c in password):
            return False, "Пароль должен содержать цифры"

        if not any(c.isalpha() for c in password):
            return False, "Пароль должен содержать буквы"

        special_chars = "!@#$%^&*"
        if not any(c in special_chars for c in password):
            return False, f"Пароль должен содержать специальные символы ({special_chars})"

        return True, "Пароль надежный"


class UserManager:
    """Менеджер пользователей"""

    def __init__(self):
        self.users_file = AppPaths.USERS_FILE
        self.users = self.load_users()
        self.hasher = PasswordHasher()

    def load_users(self) -> Dict:
        """Загрузка пользователей из файла"""
        default_users = {
            "Иван_Петров": {
                "password": PasswordHasher().hash_password("User123!"),
                "role": "admin",
                "full_name": "Иван Петров",
                "email": "ivan.petrov@company.com",
                "department": "IT",
                "created": "2024-01-15",
                "last_login": "",
                "avatar_color": "#3498db"
            },
            "Анна_Сидорова": {
                "password": PasswordHasher().hash_password("Anna2024!"),
                "role": "editor",
                "full_name": "Анна Сидорова",
                "email": "anna.sidorova@company.com",
                "department": "Редакция",
                "created": "2024-02-20",
                "last_login": "",
                "avatar_color": "#e74c3c"
            }
        }

        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                return users
            except Exception as e:
                print(f"Ошибка загрузки пользователей: {e}")
                return default_users
        else:
            self.save_users(default_users)
            return default_users

    def save_users(self, users: Optional[Dict] = None):
        """Сохранение пользователей в файл"""
        if users is None:
            users = self.users

        # Создаем резервную копию
        self._create_backup()

        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения пользователей: {e}")
            raise

    def _create_backup(self):
        """Создание резервной копии файла пользователей"""
        if self.users_file.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = AppPaths.BACKUPS_DIR / f"users_backup_{timestamp}.json"
            import shutil
            shutil.copy2(self.users_file, backup_file)

    def add_user(self, username: str, password: str, **kwargs) -> Tuple[bool, str]:
        """Добавление нового пользователя"""
        if username in self.users:
            return False, "Пользователь с таким именем уже существует"

        # Валидация пароля
        is_valid, message = self.hasher.validate_password_complexity(password)
        if not is_valid:
            return False, message

        # Создание пользователя
        self.users[username] = {
            "password": self.hasher.hash_password(password),
            "role": kwargs.get("role", "user"),
            "full_name": kwargs.get("full_name", username),
            "email": kwargs.get("email", ""),
            "department": kwargs.get("department", ""),
            "created": datetime.now().isoformat(),
            "last_login": "",
            "avatar_color": self._generate_avatar_color(username)
        }

        self.save_users()
        return True, "Пользователь успешно создан"

    def authenticate(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Аутентификация пользователя"""
        if username not in self.users:
            return False, "Пользователь не найден", None

        user = self.users[username]

        if not self.hasher.verify_password(user["password"], password):
            return False, "Неверный пароль", None

        # Обновляем время последнего входа
        user["last_login"] = datetime.now().isoformat()
        self.save_users()

        return True, "Успешная аутентификация", user

    def get_user(self, username: str) -> Optional[Dict]:
        """Получение информации о пользователе"""
        return self.users.get(username)

    def update_user(self, username: str, **kwargs) -> bool:
        """Обновление информации о пользователе"""
        if username not in self.users:
            return False

        user = self.users[username]
        user.update(kwargs)
        self.save_users()
        return True

    def delete_user(self, username: str) -> bool:
        """Удаление пользователя"""
        if username not in self.users:
            return False

        del self.users[username]
        self.save_users()
        return True

    def list_users(self) -> List[Tuple[str, Dict]]:
        """Список всех пользователей"""
        return list(self.users.items())

    def get_user_count(self) -> Dict[str, int]:
        """Статистика по пользователям"""
        roles_count = {}
        for user in self.users.values():
            role = user.get("role", "unknown")
            roles_count[role] = roles_count.get(role, 0) + 1
        return roles_count

    @staticmethod
    def _generate_avatar_color(username: str) -> str:
        """Генерация цвета для аватара"""
        colors = [
            '#3498db', '#e74c3c', '#2ecc71', '#f39c12',
            '#9b59b6', '#1abc9c', '#d35400', '#c0392b'
        ]
        hash_val = sum(ord(c) for c in username)
        return colors[hash_val % len(colors)]


class LoginLogger:
    """Логирование попыток входа"""

    def __init__(self):
        self.log_file = AppPaths.LOG_FILE

    def log_attempt(self, username: str, status: str, ip_address: str = "local"):
        """Логирование попытки входа"""
        try:
            file_exists = self.log_file.exists()

            with open(self.log_file, 'a', encoding='utf-8', newline='') as f:
                fieldnames = ["timestamp", "username", "status", "ip_address"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                writer.writerow({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "username": username,
                    "status": status,
                    "ip_address": ip_address
                })
        except Exception as e:
            print(f"Ошибка записи лога: {e}")

    def get_recent_failures(self, ip_address: str, limit: int = 20) -> List[Dict]:
        """Получение последних неудачных попыток для IP"""
        failures = []

        if not self.log_file.exists():
            return failures

        try:
            with open(self.log_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                # Фильтруем последние записи
                for row in rows[-limit:]:
                    if (row.get("ip_address") == ip_address and
                            row.get("status") == "FAILURE"):
                        failures.append(row)
        except Exception as e:
            print(f"Ошибка чтения лога: {e}")

        return failures


class SessionManager:
    """Управление сессиями"""

    def __init__(self):
        self.active_sessions = {}
        self.user_manager = UserManager()
        self.logger = LoginLogger()

    def create_session(self, username: str, user_info: Dict) -> str:
        """Создание новой сессии"""
        session_id = secrets.token_hex(16)
        self.active_sessions[session_id] = {
            "username": username,
            "user_info": user_info,
            "created": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        return session_id

    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Проверка валидности сессии"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["last_activity"] = datetime.now().isoformat()
            return self.active_sessions[session_id]
        return None

    def end_session(self, session_id: str):
        """Завершение сессии"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Очистка устаревших сессий"""
        current_time = datetime.now()
        expired = []

        for session_id, session_data in self.active_sessions.items():
            created = datetime.fromisoformat(session_data["created"])
            age_hours = (current_time - created).total_seconds() / 3600

            if age_hours > max_age_hours:
                expired.append(session_id)

        for session_id in expired:
            del self.active_sessions[session_id]