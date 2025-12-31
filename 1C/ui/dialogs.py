"""
Диалоговые окна приложения
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
from datetime import datetime


def show_documents_dialog(parent, doc_manager, on_document_select):
    """Диалог списка документов"""
    dialog = tk.Toplevel(parent)
    dialog.title("Управление документами")
    dialog.geometry("700x500")
    dialog.transient(parent)
    dialog.grab_set()

    # Заголовок
    tk.Label(dialog, text="Документы",
             font=("Arial", 16, "bold")).pack(pady=10)

    # Панель инструментов
    toolbar = tk.Frame(dialog, bg='#f0f0f0')
    toolbar.pack(fill=tk.X, padx=10, pady=5)

    # Таблица
    table_frame = tk.Frame(dialog)
    table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    # Создаем Treeview
    columns = ("name", "size", "modified", "created")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

    # Настраиваем колонки
    tree.heading("name", text="Имя документа")
    tree.heading("size", text="Размер")
    tree.heading("modified", text="Изменен")
    tree.heading("created", text="Создан")

    tree.column("name", width=250)
    tree.column("size", width=100)
    tree.column("modified", width=120)
    tree.column("created", width=120)

    # Полоса прокрутки
    scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Заполняем таблицу
    def refresh_table():
        """Обновление таблицы"""
        for item in tree.get_children():
            tree.delete(item)

        docs = doc_manager.list_documents()
        for doc in docs:
            tree.insert("", tk.END, values=(
                doc["name"],
                format_file_size(doc["size"]),
                doc["modified"].strftime("%d.%m.%Y %H:%M"),
                doc["created"].strftime("%d.%m.%Y %H:%M")
            ), tags=(doc["path"],))

    refresh_table()

    # Функции кнопок
    def open_selected():
        """Открыть выбранный документ"""
        selection = tree.selection()
        if selection:
            item = selection[0]
            doc_path = tree.item(item, "tags")[0]
            on_document_select(doc_path)
            dialog.destroy()

    def delete_selected():
        """Удалить выбранный документ"""
        selection = tree.selection()
        if selection:
            item = selection[0]
            doc_path = tree.item(item, "tags")[0]
            doc_name = tree.item(item, "values")[0]

            response = messagebox.askyesno(
                "Удаление",
                f"Удалить документ '{doc_name}'?\nЭто действие нельзя отменить."
            )

            if response:
                if doc_manager.delete_document(doc_path):
                    refresh_table()
                    messagebox.showinfo("Успех", "Документ удален")
                else:
                    messagebox.showerror("Ошибка", "Не удалось удалить документ")

    # Кнопки
    tk.Button(toolbar, text="📂 Открыть",
              command=open_selected,
              bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=2)

    tk.Button(toolbar, text="🗑 Удалить",
              command=delete_selected,
              bg="#f44336", fg="white").pack(side=tk.LEFT, padx=2)

    tk.Button(toolbar, text="🔄 Обновить",
              command=refresh_table,
              bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=2)

    # Привязка двойного клика
    tree.bind('<Double-Button-1>', lambda e: open_selected())

    # Кнопка закрытия
    tk.Button(dialog, text="Закрыть",
              command=dialog.destroy,
              bg="#9E9E9E", fg="white").pack(pady=10)


def show_find_dialog(parent, text_widget):
    """Диалог поиска текста"""
    dialog = tk.Toplevel(parent)
    dialog.title("Поиск текста")
    dialog.geometry("400x200")
    dialog.transient(parent)
    dialog.grab_set()

    tk.Label(dialog, text="Найти:").pack(pady=10)

    find_var = tk.StringVar()
    find_entry = tk.Entry(dialog, textvariable=find_var, width=40)
    find_entry.pack(pady=5)

    case_var = tk.BooleanVar()
    case_check = tk.Checkbutton(dialog, text="Учитывать регистр",
                                variable=case_var)
    case_check.pack(pady=5)

    def find():
        """Поиск текста"""
        search_term = find_var.get()
        if not search_term:
            return

        content = text_widget.get('1.0', tk.END)

        # Удаляем предыдущее выделение
        text_widget.tag_remove('found', '1.0', tk.END)

        if case_var.get():
            # Поиск с учетом регистра
            start_pos = '1.0'
            while True:
                start_pos = text_widget.search(search_term, start_pos,
                                               stopindex=tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_term)}c"
                text_widget.tag_add('found', start_pos, end_pos)
                start_pos = end_pos
        else:
            # Поиск без учета регистра
            content_lower = content.lower()
            search_term_lower = search_term.lower()
            pos = 0

            while True:
                pos = content_lower.find(search_term_lower, pos)
                if pos == -1:
                    break

                start_pos = f"1.0+{pos}c"
                end_pos = f"1.0+{pos + len(search_term)}c"
                text_widget.tag_add('found', start_pos, end_pos)
                pos += 1

        # Настройка выделения
        text_widget.tag_config('found', background='yellow', foreground='black')

        if text_widget.tag_ranges('found'):
            # Прокручиваем к первому совпадению
            text_widget.see('found.first')
            messagebox.showinfo("Поиск", f"Найдено совпадений: {len(text_widget.tag_ranges('found')) // 2}")
        else:
            messagebox.showinfo("Поиск", "Текст не найден")

    tk.Button(dialog, text="Найти", command=find,
              bg="#4CAF50", fg="white").pack(pady=10)

    find_entry.focus_set()
    dialog.bind('<Return>', lambda e: find())


def show_replace_dialog(parent, text_widget):
    """Диалог замены текста"""
    dialog = tk.Toplevel(parent)
    dialog.title("Замена текста")
    dialog.geometry("400x300")
    dialog.transient(parent)
    dialog.grab_set()

    tk.Label(dialog, text="Найти:").pack(pady=5)

    find_var = tk.StringVar()
    find_entry = tk.Entry(dialog, textvariable=find_var, width=40)
    find_entry.pack(pady=5)

    tk.Label(dialog, text="Заменить на:").pack(pady=5)

    replace_var = tk.StringVar()
    replace_entry = tk.Entry(dialog, textvariable=replace_var, width=40)
    replace_entry.pack(pady=5)

    case_var = tk.BooleanVar()
    case_check = tk.Checkbutton(dialog, text="Учитывать регистр",
                                variable=case_var)
    case_check.pack(pady=5)

    def replace():
        """Замена текста"""
        find_text = find_var.get()
        replace_text = replace_var.get()

        if not find_text:
            return

        content = text_widget.get('1.0', tk.END)

        if case_var.get():
            new_content = content.replace(find_text, replace_text)
        else:
            # Без учета регистра
            import re
            pattern = re.compile(re.escape(find_text), re.IGNORECASE)
            new_content = pattern.sub(replace_text, content)

        text_widget.delete('1.0', tk.END)
        text_widget.insert('1.0', new_content)
        messagebox.showinfo("Замена", "Замена выполнена")

    tk.Button(dialog, text="Заменить", command=replace,
              bg="#4CAF50", fg="white").pack(pady=10)

    find_entry.focus_set()
    dialog.bind('<Return>', lambda e: replace())


def format_file_size(size_bytes):
    """Форматирование размера файла"""
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} ТБ"