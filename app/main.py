import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import random
import os
import db_utils

# Класс для капчи-пазла 
class PuzzleCaptcha:
    def __init__(self, parent, fragments_paths, size=150):
        self.parent = parent
        self.correct_order = list(range(4))
        self.current_order = self.correct_order.copy()
        random.shuffle(self.current_order)

        self.pieces = []
        for path in fragments_paths:
            img = Image.open(path).resize((size, size))
            self.pieces.append(ImageTk.PhotoImage(img))

        self.selected = None
        self.create_widgets()

    def create_widgets(self):
        self.buttons = []
        for idx in range(4):
            btn = tk.Button(self.parent, image=self.pieces[self.current_order[idx]],
                            command=lambda i=idx: self.on_click(i))
            btn.grid(row=idx//2, column=idx%2, padx=2, pady=2)
            self.buttons.append(btn)

    def on_click(self, idx):
        if self.selected is None:
            self.selected = idx
            self.buttons[idx].config(relief=tk.SUNKEN)
        else:
            self.swap(self.selected, idx)
            self.selected = None
            for btn in self.buttons:
                btn.config(relief=tk.RAISED)

    def swap(self, i, j):
        self.current_order[i], self.current_order[j] = self.current_order[j], self.current_order[i]
        self.buttons[i].config(image=self.pieces[self.current_order[i]])
        self.buttons[j].config(image=self.pieces[self.current_order[j]])

    def is_solved(self):
        return self.current_order == self.correct_order

    def reset(self):
        random.shuffle(self.current_order)
        for idx, btn in enumerate(self.buttons):
            btn.config(image=self.pieces[self.current_order[idx]], relief=tk.RAISED)
        self.selected = None

# Окно авторизации 
class LoginWindow:
    def __init__(self, fragments):
        self.fragments = fragments
        self.window = tk.Tk()
        self.window.title("Молочный комбинат - Авторизация")
        self.window.minsize(400, 500)
        self.window.resizable(True, True)

        tk.Label(self.window, text="Логин:").pack(pady=(20,0))
        self.entry_login = tk.Entry(self.window)
        self.entry_login.pack()
        self.entry_login.focus()

        tk.Label(self.window, text="Пароль:").pack(pady=(10,0))
        self.entry_password = tk.Entry(self.window, show="*")
        self.entry_password.pack()

        frame_captcha = tk.Frame(self.window)
        frame_captcha.pack(pady=20)
        self.captcha = PuzzleCaptcha(frame_captcha, self.fragments)

        self.btn_login = tk.Button(self.window, text="Войти", state=tk.DISABLED,
                                   command=self.check_login)
        self.btn_login.pack(pady=20)

        self.check_puzzle()
        self.window.mainloop()

    def check_puzzle(self):
        if self.captcha.is_solved():
            self.btn_login.config(state=tk.NORMAL)
        else:
            self.btn_login.config(state=tk.DISABLED)
        self.window.after(100, self.check_puzzle)

    def check_login(self):
        login = self.entry_login.get().strip()
        password = self.entry_password.get().strip()

        if not login or not password:
            messagebox.showerror("Ошибка", "Заполните оба поля!")
            return

        conn = None
        try:
            conn = db_utils.get_connection()
            user = db_utils.get_user(login)
            if not user:
                messagebox.showerror("Ошибка", "Вы ввели неверный логин или пароль. Пожалуйста проверьте ещё раз введенные данные")
                self.record_failed_attempt(login, None, conn)
                self.captcha.reset()
                return

            user_id, db_password, role, is_blocked, failed_attempts = user

            if is_blocked:
                messagebox.showerror("Доступ запрещён", "Вы заблокированы. Обратитесь к администратору.")
                return

            if db_password != password:
                messagebox.showerror("Ошибка", "Вы ввели неверный логин или пароль. Пожалуйста проверьте ещё раз введенные данные")
                self.record_failed_attempt(login, user_id, conn)
                self.captcha.reset()
                return

            db_utils.reset_failed_attempts(user_id, conn)

            messagebox.showinfo("Успех", "Вы успешно авторизовались")
            self.window.destroy()
            if role == 'admin':
                AdminWindow(login)
            else:
                UserWindow(login)

        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e))
        finally:
            if conn:
                conn.close()

    def record_failed_attempt(self, login, user_id, conn):
        if user_id:
            new_count = db_utils.update_failed_attempts(user_id, conn)
            if new_count >= 3:
                db_utils.block_user(user_id, conn)
                messagebox.showerror("Блокировка", "Учётная запись заблокирована за 3 неудачные попытки.")
        conn.commit()

# Окно администратора
class AdminWindow:
    def __init__(self, current_user):
        self.current_user = current_user
        self.window = tk.Tk()
        self.window.title("Молочный комбинат - Администратор")
        self.window.minsize(800, 500)
        self.window.geometry("800x500")

        tk.Label(self.window, text=f"Добро пожаловать, {current_user} (администратор)",
                 font=("Arial", 14)).pack(pady=10)

        frame_list = tk.Frame(self.window)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(frame_list, columns=("id", "login", "role", "blocked", "attempts"),
                                  show="headings")
        
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("login", width=150)
        self.tree.column("role", width=100)
        self.tree.column("blocked", width=100, anchor="center")
        self.tree.column("attempts", width=80, anchor="center")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("login", text="Логин")
        self.tree.heading("role", text="Роль")
        self.tree.heading("blocked", text="Заблокирован")
        self.tree.heading("attempts", text="Попытки")
        self.tree.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Добавить", command=self.add_user).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Редактировать", command=self.edit_user).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Снять блокировку", command=self.unblock_user).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Выход", command=self.window.destroy).pack(side=tk.LEFT, padx=5)

        self.refresh_users()
        self.window.mainloop()

    def refresh_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        users = db_utils.get_all_users()
        for user in users:
            blocked = "Да" if user[3] else "Нет"
            self.tree.insert("", tk.END, values=(user[0], user[1], user[2], blocked, user[4]))

    def add_user(self):
        AddEditUser(self.refresh_users)

    def edit_user(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите пользователя для редактирования")
            return
        user_id = self.tree.item(selected[0])['values'][0]
        AddEditUser(self.refresh_users, user_id)

    def unblock_user(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите пользователя")
            return
        user_id = self.tree.item(selected[0])['values'][0]
        conn = db_utils.get_connection()
        db_utils.unblock_user(user_id, conn)
        conn.close()
        self.refresh_users()
        messagebox.showinfo("Успех", "Пользователь разблокирован")

# Диалог добавления/редактирования
class AddEditUser:
    def __init__(self, refresh_callback, user_id=None):
        self.refresh_callback = refresh_callback
        self.user_id = user_id
        self.window = tk.Toplevel()
        if user_id is None:
            self.window.title("Молочный комбинат - Добавление пользователя")
        else:
            self.window.title("Молочный комбинат - Редактирование пользователя")
        self.window.geometry("350x350")
        self.window.grab_set()

        tk.Label(self.window, text="Логин:").pack(pady=(10,0))
        self.entry_login = tk.Entry(self.window)
        self.entry_login.pack()
        
        tk.Label(self.window, text="Пароль:").pack(pady=(5,0))
        self.entry_password = tk.Entry(self.window, show="*")
        self.entry_password.pack()
        
        tk.Label(self.window, text="Роль:").pack(pady=(5,0))
        self.role_var = tk.StringVar(value="user")
        role_menu = ttk.Combobox(self.window, textvariable=self.role_var,
                                 values=["user", "admin"], state="readonly")
        role_menu.pack()
        
        self.blocked_var = tk.BooleanVar(value=False)
        self.blocked_check = tk.Checkbutton(self.window, text="Заблокирован", 
                                           variable=self.blocked_var)
        self.blocked_check.pack(pady=(10,0))
        
        if user_id:
            conn = db_utils.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT login, role, is_blocked FROM users WHERE id = %s", (user_id,))
            login, role, is_blocked = cur.fetchone()
            self.entry_login.insert(0, login)
            self.role_var.set(role)
            self.blocked_var.set(is_blocked)
            self.entry_login.config(state='disabled')
            conn.close()
            
            if login == self.refresh_callback.__self__.current_user:
                self.role_menu = role_menu
                self.role_menu.config(state='disabled')
                self.blocked_check.config(state='disabled')
                tk.Label(self.window, text="(Нельзя изменить свои данные)", 
                        fg="red").pack()
        
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", command=self.window.destroy).pack(side=tk.LEFT, padx=5)

    def save(self):
        login = self.entry_login.get().strip()
        password = self.entry_password.get().strip()
        role = self.role_var.get()
        is_blocked = self.blocked_var.get()

        if not login or not password:
            messagebox.showerror("Ошибка", "Логин и пароль обязательны")
            return

        conn = None
        try:
            if self.user_id is None:
                success = db_utils.add_user(login, password, role)
                if not success:
                    messagebox.showerror("Ошибка", "Пользователь с таким логином уже существует")
                    return
            else:
                conn = db_utils.get_connection()
                cur = conn.cursor()
                cur.execute("UPDATE users SET password = %s, role = %s, is_blocked = %s WHERE id = %s",
                           (password, role, is_blocked, self.user_id))
                conn.commit()
                conn.close()
                
            messagebox.showinfo("Успех", "Пользователь сохранён")
            self.refresh_callback()
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e))
            if conn:
                conn.close()

# Окно обычного пользователя
class UserWindow:
    def __init__(self, current_user):
        self.window = tk.Tk()
        self.window.title("Молочный комбинат - Пользователь")
        self.window.minsize(400, 200)
        self.window.geometry("400x200")

        tk.Label(self.window, text=f"Добро пожаловать, {current_user} (пользователь)",
                 font=("Arial", 14)).pack(pady=20)
        tk.Label(self.window, text="Здесь может быть функционал для пользователя").pack()
        tk.Button(self.window, text="Выход", command=self.window.destroy).pack(pady=20)
        self.window.mainloop()

# Запуск
if __name__ == "__main__":
    fragments = [r"app\1.png",
                 r"app\2.png",
                 r"app\3.png",
                 r"app\4.png"]
    for f in fragments:
        if not os.path.exists(f):
            print(f"Ошибка: файл {f} не найден. Программа будет закрыта.")
            exit(1)
    LoginWindow(fragments)