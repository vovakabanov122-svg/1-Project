"""
Основной функционал текстового редактора
"""
import os
import glob
import uuid
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict

from config import AppPaths, AppConfig


class DocumentManager:
    """Менеджер документов"""

    def __init__(self):
        self.docs_dir = AppPaths.DOCS_DIR

    def create_document(self, content: str = "") -> str:
        """Создание нового документа"""
        doc_id = str(uuid.uuid4())[:8]
        filename = f"doc_{doc_id}.txt"
        filepath = self.docs_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(filepath)

    def save_document(self, filepath: str, content: str) -> bool:
        """Сохранение документа"""
        try:
            # Создаем резервную копию если файл существует
            if Path(filepath).exists():
                self._create_backup(filepath)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Ошибка сохранения документа: {e}")
            return False

    def load_document(self, filepath: str) -> Optional[str]:
        """Загрузка документа"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Ошибка загрузки документа: {e}")
            return None

    def delete_document(self, filepath: str) -> bool:
        """Удаление документа"""
        try:
            Path(filepath).unlink()
            return True
        except Exception as e:
            print(f"Ошибка удаления документа: {e}")
            return False

    def rename_document(self, old_path: str, new_name: str) -> Optional[str]:
        """Переименование документа"""
        try:
            old_path_obj = Path(old_path)

            # Добавляем расширение если не указано
            if not new_name.endswith('.txt'):
                new_name += '.txt'

            new_path = old_path_obj.parent / new_name

            # Проверяем существование
            if new_path.exists():
                return None

            old_path_obj.rename(new_path)
            return str(new_path)
        except Exception as e:
            print(f"Ошибка переименования: {e}")
            return None

    def list_documents(self) -> List[Dict]:
        """Список всех документов"""
        docs = []

        for filepath in glob.glob(str(self.docs_dir / "*.txt")):
            try:
                stat = Path(filepath).stat()
                docs.append({
                    "path": filepath,
                    "name": Path(filepath).name,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime),
                    "modified": datetime.fromtimestamp(stat.st_mtime)
                })
            except Exception as e:
                print(f"Ошибка получения информации о файле {filepath}: {e}")

        # Сортируем по дате изменения
        docs.sort(key=lambda x: x["modified"], reverse=True)
        return docs

    def get_document_stats(self) -> Dict:
        """Статистика по документам"""
        docs = self.list_documents()
        total_size = sum(doc["size"] for doc in docs)

        return {
            "count": len(docs),
            "total_size": total_size,
            "avg_size": total_size // len(docs) if docs else 0,
            "oldest": docs[-1]["modified"] if docs else None,
            "newest": docs[0]["modified"] if docs else None
        }

    def _create_backup(self, filepath: str):
        """Создание резервной копии"""
        backup_dir = AppPaths.BACKUPS_DIR / "documents"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = Path(filepath).name
        backup_file = backup_dir / f"{filename}.backup_{timestamp}"

        shutil.copy2(filepath, backup_file)

        # Удаляем старые бэкапы
        self._cleanup_old_backups(backup_dir)

    def _cleanup_old_backups(self, backup_dir: Path, keep_count: int = 10):
        """Очистка старых резервных копий"""
        backups = sorted(backup_dir.glob("*.backup_*"))

        if len(backups) > keep_count:
            for backup in backups[:-keep_count]:
                backup.unlink()


class TextAnalyzer:
    """Анализ текста"""

    @staticmethod
    def analyze_text(text: str) -> Dict:
        """Анализ текста"""
        words = text.split()
        lines = text.split('\n')

        return {
            "characters": len(text),
            "words": len(words),
            "lines": len(lines),
            "spaces": text.count(' '),
            "sentences": len(re.split(r'[.!?]+', text)),
            "avg_word_length": sum(len(word) for word in words) / len(words) if words else 0,
            "avg_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0
        }

    @staticmethod
    def find_text(text: str, search_term: str, case_sensitive: bool = False) -> List[Tuple[int, int]]:
        """Поиск текста"""
        if not case_sensitive:
            text = text.lower()
            search_term = search_term.lower()

        positions = []
        start = 0

        while True:
            pos = text.find(search_term, start)
            if pos == -1:
                break
            positions.append((pos, pos + len(search_term)))
            start = pos + 1

        return positions

    @staticmethod
    def replace_text(text: str, old_text: str, new_text: str,
                     case_sensitive: bool = False, count: int = -1) -> str:
        """Замена текста"""
        if not case_sensitive:
            # Используем регулярное выражение с флагом игнорирования регистра
            pattern = re.compile(re.escape(old_text), re.IGNORECASE)
            result, replacements = pattern.subn(new_text, text, count)
            return result
        else:
            return text.replace(old_text, new_text, count)