import tkinter as tk
from login_form import LoginForm

def start_main_app_from_login(username, role):
    """Колбэк для запуска редактора из формы логина"""
    # Отложенный импорт для избежания циклической зависимости
    import app_main
    app_main.start_app(username, role)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Текстовый редактор Pro - Вход в систему")

    # Передаем колбэк для запуска редактора
    app = LoginForm(master=root, on_login_success=start_main_app_from_login)
    app.pack(fill='both', expand=True)
    root.mainloop()