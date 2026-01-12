import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime
import os
import mysql.connector
from mysql.connector import Error
import configparser

class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Библиотекарь - Система учета книг")
        self.root.geometry("1920x900")

        # Путь к файлу конфигурации
        self.config_file = "db_config.ini"
        
        # Загрузка конфигурации БД
        self.db_config = self.load_db_config()
        
        # Подключение к БД
        self.connection = None
        self.cursor = None
        self.connect_to_db()
        
        # Инициализация таблицы, если её нет
        self.init_database()
        
        # Загрузка данных из БД
        self.books = self.load_data_from_db()

        # Стилизация
        self.setup_styles()

        # Создание интерфейса
        self.create_widgets()

        # Обновление таблицы
        self.update_table()

    def load_db_config(self):
        """Загрузка конфигурации базы данных"""
        config = configparser.ConfigParser()
        
        # Значения по умолчанию
        default_config = {
            'database': {
                'host': 'localhost',
                'user': 'root',
                'password': '',
                'database': 'library_db',
                'port': '3306'
            }
        }
        
        if os.path.exists(self.config_file):
            config.read(self.config_file)
        else:
            config.read_dict(default_config)
            # Создание файла конфигурации с настройками по умолчанию
            with open(self.config_file, 'w') as configfile:
                config.write(configfile)
        
        return config['database']

    def connect_to_db(self):
        """Подключение к базе данных MySQL"""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                port=int(self.db_config.get('port', '3306'))
            )
            
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                print("Успешно подключено к базе данных MySQL")
                
        except Error as e:
            print(f"Ошибка подключения к базе данных: {e}")
            messagebox.showerror(
                "Ошибка подключения", 
                f"Не удалось подключиться к базе данных.\nОшибка: {e}\n\nПроверьте настройки подключения."
            )
            
            # Открываем окно настройки подключения
            self.open_db_config_dialog()
            
            # Пробуем подключиться снова
            self.connect_to_db()

    def open_db_config_dialog(self):
        """Открытие диалогового окна для настройки подключения к БД"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Настройка подключения к БД")
        config_window.geometry("400x300")
        config_window.transient(self.root)
        config_window.grab_set()
        
        tk.Label(config_window, text="Настройки подключения к MySQL", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        fields = [
            ("Хост:", "host"),
            ("Пользователь:", "user"),
            ("Пароль:", "password"),
            ("База данных:", "database"),
            ("Порт:", "port")
        ]
        
        entries = {}
        for i, (label_text, field_name) in enumerate(fields):
            frame = tk.Frame(config_window)
            frame.pack(fill=tk.X, padx=20, pady=5)
            
            tk.Label(frame, text=label_text, width=15, anchor="w").pack(side=tk.LEFT)
            
            entry = tk.Entry(frame, width=25)
            entry.pack(side=tk.RIGHT, padx=10)
            entry.insert(0, self.db_config.get(field_name, ""))
            entries[field_name] = entry
        
        def save_config():
            for field_name, entry in entries.items():
                self.db_config[field_name] = entry.get()
            
            # Сохраняем конфигурацию
            config = configparser.ConfigParser()
            config['database'] = self.db_config
            
            with open(self.config_file, 'w') as configfile:
                config.write(configfile)
            
            messagebox.showinfo("Сохранено", "Настройки сохранены!")
            config_window.destroy()
        
        tk.Button(config_window, text="Сохранить", command=save_config, 
                 bg="#3498db", fg="white", padx=20, pady=5).pack(pady=20)

    def init_database(self):
        """Инициализация таблиц в базе данных"""
        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                author VARCHAR(255) NOT NULL,
                year INT NOT NULL,
                genre VARCHAR(100),
                publisher VARCHAR(255),
                isbn VARCHAR(20),
                quantity INT DEFAULT 1,
                location VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            self.cursor.execute(create_table_query)
            self.connection.commit()
            print("Таблица 'books' создана или уже существует")
            
        except Error as e:
            print(f"Ошибка при создании таблицы: {e}")

    def load_data_from_db(self):
        """Загрузка данных из базы данных"""
        try:
            query = "SELECT * FROM books ORDER BY title"
            self.cursor.execute(query)
            books = self.cursor.fetchall()
            
            # Преобразование в список словарей
            result = []
            for book in books:
                # Преобразование Decimal и datetime в обычные типы
                book_dict = {}
                for key, value in book.items():
                    if hasattr(value, 'isoformat'):  # Для datetime объектов
                        book_dict[key] = value.isoformat()
                    else:
                        book_dict[key] = str(value) if value is not None else ""
                result.append(book_dict)
            
            return result
            
        except Error as e:
            print(f"Ошибка при загрузке данных: {e}")
            return []

    def save_data_to_db(self, book_data, operation='insert'):
        """Сохранение данных в базу данных"""
        try:
            if operation == 'insert':
                query = """
                INSERT INTO books (title, author, year, genre, publisher, isbn, quantity, location)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    book_data['title'],
                    book_data['author'],
                    book_data['year'],
                    book_data.get('genre', ''),
                    book_data.get('publisher', ''),
                    book_data.get('isbn', ''),
                    book_data.get('quantity', 1),
                    book_data.get('location', '')
                )
                self.cursor.execute(query, values)
                book_id = self.cursor.lastrowid
                
            elif operation == 'update':
                query = """
                UPDATE books 
                SET title = %s, author = %s, year = %s, genre = %s, 
                    publisher = %s, isbn = %s, quantity = %s, location = %s
                WHERE id = %s
                """
                values = (
                    book_data['title'],
                    book_data['author'],
                    book_data['year'],
                    book_data.get('genre', ''),
                    book_data.get('publisher', ''),
                    book_data.get('isbn', ''),
                    book_data.get('quantity', 1),
                    book_data.get('location', ''),
                    self.selected_book_id
                )
                self.cursor.execute(query, values)
                book_id = self.selected_book_id
                
            self.connection.commit()
            return book_id
            
        except Error as e:
            print(f"Ошибка при сохранении данных: {e}")
            self.connection.rollback()
            return None

    def delete_from_db(self, book_id):
        """Удаление книги из базы данных"""
        try:
            query = "DELETE FROM books WHERE id = %s"
            self.cursor.execute(query, (book_id,))
            self.connection.commit()
            return True
            
        except Error as e:
            print(f"Ошибка при удалении данных: {e}")
            self.connection.rollback()
            return False

    def search_in_db(self, field, value):
        """Поиск книг в базе данных"""
        try:
            # Безопасное формирование запроса
            allowed_fields = ['title', 'author', 'genre', 'isbn', 'year']
            if field not in allowed_fields:
                field = 'title'
            
            query = f"SELECT * FROM books WHERE {field} LIKE %s ORDER BY title"
            self.cursor.execute(query, (f"%{value}%",))
            books = self.cursor.fetchall()
            
            # Преобразование в список словарей
            result = []
            for book in books:
                book_dict = {}
                for key, value in book.items():
                    if hasattr(value, 'isoformat'):
                        book_dict[key] = value.isoformat()
                    else:
                        book_dict[key] = str(value) if value is not None else ""
                result.append(book_dict)
            
            return result
            
        except Error as e:
            print(f"Ошибка при поиске данных: {e}")
            return []

    def setup_styles(self):
        """Настройка стилей приложения"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.bg_color = "#f0f4f7"
        self.fg_color = "#333333"
        self.accent_color = "#2c3e50"
        self.button_color = "#3498db"
        self.delete_color = "#e74c3c"
        self.edit_color = "#f39c12"
        self.root.configure(bg=self.bg_color)

    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Заголовок
        header_frame = tk.Frame(self.root, bg=self.accent_color, height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="📚 Библиотекарь - Система учета книг (MySQL)",
            font=("Arial", 20, "bold"),
            bg=self.accent_color,
            fg="white"
        )
        title_label.pack(pady=20)

        # Кнопка настройки БД в заголовке
        db_button = tk.Button(
            header_frame,
            text="Настройка БД",
            command=self.open_db_config_dialog,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 10),
            padx=10,
            pady=5
        )
        db_button.place(x=20, y=20)

        # Основной контейнер
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Левая панель
        left_panel = tk.Frame(main_container, bg=self.bg_color)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        form_frame = tk.LabelFrame(
            left_panel,
            text="Данные книги",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.accent_color,
            padx=15,
            pady=15
        )
        form_frame.pack(fill=tk.X, pady=(0, 20))

        fields = [
            ("Название:", "title"),
            ("Автор:", "author"),
            ("Год издания:", "year"),
            ("Жанр:", "genre"),
            ("Издательство:", "publisher"),
            ("ISBN:", "isbn"),
            ("Количество экземпляров:", "quantity"),
            ("Место нахождения:", "location")
        ]

        self.entries = {}
        for i, (label_text, field_name) in enumerate(fields):
            label = tk.Label(
                form_frame,
                text=label_text,
                font=("Arial", 10),
                bg=self.bg_color,
                fg=self.fg_color,
                anchor="w"
            )
            label.grid(row=i, column=0, sticky="w", pady=5)

            entry = tk.Entry(
                form_frame,
                font=("Arial", 10),
                width=30
            )
            entry.grid(row=i, column=1, pady=5, padx=(10, 0))
            self.entries[field_name] = entry

        # Кнопки формы
        button_frame = tk.Frame(form_frame, bg=self.bg_color)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=15)

        self.add_button = tk.Button(
            button_frame,
            text="Добавить книгу",
            command=self.add_book,
            bg=self.button_color,
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            padx=10,
            pady=8
        )
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.update_button = tk.Button(
            button_frame,
            text="Обновить",
            command=self.update_book,
            bg=self.edit_color,
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            padx=10,
            pady=8,
            state=tk.DISABLED
        )
        self.update_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = tk.Button(
            button_frame,
            text="Очистить",
            command=self.clear_form,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            padx=10,
            pady=8
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # Поиск
        search_frame = tk.LabelFrame(
            left_panel,
            text="Поиск книги",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.accent_color,
            padx=15,
            pady=15
        )
        search_frame.pack(fill=tk.X)

        search_label = tk.Label(
            search_frame,
            text="Поиск по:",
            font=("Arial", 10),
            bg=self.bg_color,
            fg=self.fg_color
        )
        search_label.grid(row=0, column=0, sticky="w", pady=5)

        self.search_var = tk.StringVar()
        self.search_var.set("title")

        search_options = ["title", "author", "genre", "isbn", "year"]
        search_menu = ttk.OptionMenu(
            search_frame,
            self.search_var,
            "title",
            *search_options
        )
        search_menu.grid(row=0, column=1, padx=(10, 0), pady=5)

        self.search_entry = tk.Entry(
            search_frame,
            font=("Arial", 10),
            width=25
        )
        self.search_entry.grid(row=1, column=0, columnspan=2, pady=5, sticky="we")

        search_button = tk.Button(
            search_frame,
            text="Найти",
            command=self.search_books,
            bg=self.button_color,
            fg="white",
            font=("Arial", 10, "bold"),
            width=10,
            pady=5
        )
        search_button.grid(row=2, column=0, pady=10, sticky="w")

        reset_search_button = tk.Button(
            search_frame,
            text="Сбросить",
            command=self.reset_search,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            width=10,
            pady=5
        )
        reset_search_button.grid(row=2, column=1, pady=10, sticky="e")

        # Правая панель
        right_panel = tk.Frame(main_container, bg=self.bg_color)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        table_frame = tk.LabelFrame(
            right_panel,
            text="Каталог книг",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.accent_color,
            padx=15,
            pady=15
        )
        table_frame.pack(fill=tk.BOTH, expand=True)

        toolbar = tk.Frame(table_frame, bg=self.bg_color)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        stats_label = tk.Label(
            toolbar,
            text="Всего книг: 0",
            font=("Arial", 10, "bold"),
            bg=self.bg_color,
            fg=self.accent_color
        )
        stats_label.pack(side=tk.LEFT)
        self.stats_label = stats_label

        export_button = tk.Button(
            toolbar,
            text="Экспорт данных",
            command=self.export_data,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10),
            padx=10,
            pady=5
        )
        export_button.pack(side=tk.RIGHT, padx=5)

        import_button = tk.Button(
            toolbar,
            text="Импорт данных",
            command=self.import_data,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 10),
            padx=10,
            pady=5
        )
        import_button.pack(side=tk.RIGHT, padx=5)

        # Таблица
        columns = ("ID", "Название", "Автор", "Год", "Жанр", "Издательство", "ISBN", "Кол-во", "Место")

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=20,
            selectmode="browse"
        )

        column_widths = [50, 200, 150, 60, 120, 150, 120, 80, 120]
        for col, width in zip(columns, column_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, minwidth=50)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_book_select)

        action_frame = tk.Frame(table_frame, bg=self.bg_color)
        action_frame.pack(fill=tk.X, pady=(10, 0))

        delete_button = tk.Button(
            action_frame,
            text="Удалить книгу",
            command=self.delete_book,
            bg=self.delete_color,
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8
        )
        delete_button.pack(side=tk.LEFT, padx=(0, 10))

        edit_button = tk.Button(
            action_frame,
            text="Редактировать",
            command=self.edit_book,
            bg=self.edit_color,
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8
        )
        edit_button.pack(side=tk.LEFT)

        self.status_bar = tk.Label(
            self.root,
            text="Готово. Загружено книг: 0",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg=self.accent_color,
            fg="white"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.selected_book_id = None

    def update_table(self, books=None):
        """Обновление таблицы с книгами"""
        for row in self.tree.get_children():
            self.tree.delete(row)

        if books is None:
            books = self.books

        for book in books:
            values = (
                book.get("id", ""),
                book.get("title", ""),
                book.get("author", ""),
                book.get("year", ""),
                book.get("genre", ""),
                book.get("publisher", ""),
                book.get("isbn", ""),
                book.get("quantity", ""),
                book.get("location", "")
            )
            self.tree.insert("", tk.END, values=values)

        self.stats_label.config(text=f"Всего книг: {len(books)}")
        self.status_bar.config(text=f"Готово. Загружено книг: {len(books)}")

    def add_book(self):
        """Добавление новой книги в БД"""
        book_data = {}
        for field, entry in self.entries.items():
            value = entry.get().strip()
            if not value:
                messagebox.showwarning("Ошибка", f"Поле '{field}' не может быть пустым!")
                return
            book_data[field] = value

        try:
            year = int(book_data["year"])
            if year < 0 or year > datetime.now().year:
                messagebox.showwarning("Ошибка", "Укажите корректный год издания!")
                return
        except ValueError:
            messagebox.showwarning("Ошибка", "Год издания должен быть числом!")
            return

        try:
            quantity = int(book_data["quantity"])
            if quantity < 0:
                messagebox.showwarning("Ошибка", "Количество не может быть отрицательным!")
                return
        except ValueError:
            messagebox.showwarning("Ошибка", "Количество должно быть числом!")
            return

        # Сохранение в БД
        book_id = self.save_data_to_db(book_data, 'insert')
        
        if book_id:
            book_data["id"] = book_id
            self.books.append(book_data)
            self.update_table()
            self.clear_form()
            self.status_bar.config(text=f"Книга '{book_data['title']}' успешно добавлена в БД!")
            self.tree.see(self.tree.get_children()[-1])
        else:
            messagebox.showerror("Ошибка", "Не удалось добавить книгу в базу данных!")

    def update_book(self):
        """Обновление существующей книги в БД"""
        if self.selected_book_id is None:
            messagebox.showwarning("Ошибка", "Выберите книгу для обновления!")
            return

        book_data = {}
        for field, entry in self.entries.items():
            value = entry.get().strip()
            if not value:
                messagebox.showwarning("Ошибка", f"Поле '{field}' не может быть пустым!")
                return
            book_data[field] = value

        try:
            year = int(book_data["year"])
            if year < 0 or year > datetime.now().year:
                messagebox.showwarning("Ошибка", "Укажите корректный год издания!")
                return
        except ValueError:
            messagebox.showwarning("Ошибка", "Год издания должен быть числом!")
            return

        try:
            quantity = int(book_data["quantity"])
            if quantity < 0:
                messagebox.showwarning("Ошибка", "Количество не может быть отрицательным!")
                return
        except ValueError:
            messagebox.showwarning("Ошибка", "Количество должно быть числом!")
            return

        # Обновление в БД
        book_id = self.save_data_to_db(book_data, 'update')
        
        if book_id:
            book_data["id"] = book_id
            # Обновление в локальном списке
            for i, book in enumerate(self.books):
                if book.get("id") == self.selected_book_id:
                    self.books[i] = book_data
                    break
            
            self.update_table()
            self.clear_form()
            self.status_bar.config(text=f"Книга '{book_data['title']}' успешно обновлена в БД!")
            self.selected_book_id = None
            self.update_button.config(state=tk.DISABLED)
        else:
            messagebox.showerror("Ошибка", "Не удалось обновить книгу в базе данных!")

    def delete_book(self):
        """Удаление книги из БД"""
        if self.selected_book_id is None:
            messagebox.showwarning("Ошибка", "Выберите книгу для удаления!")
            return

        confirm = messagebox.askyesno(
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить выбранную книгу?"
        )

        if not confirm:
            return

        book_title = ""
        for book in self.books:
            if book.get("id") == self.selected_book_id:
                book_title = book.get("title", "")
                break

        # Удаление из БД
        if self.delete_from_db(self.selected_book_id):
            # Удаление из локального списка
            self.books = [book for book in self.books if book.get("id") != self.selected_book_id]
            
            self.update_table()
            self.clear_form()
            self.status_bar.config(text=f"Книга '{book_title}' успешно удалена из БД!")
            self.selected_book_id = None
            self.update_button.config(state=tk.DISABLED)
        else:
            messagebox.showerror("Ошибка", "Не удалось удалить книгу из базы данных!")

    def edit_book(self):
        """Редактирование выбранной книги"""
        if self.selected_book_id is None:
            messagebox.showwarning("Ошибка", "Выберите книгу для редактирования!")
            return

        for book in self.books:
            if book.get("id") == self.selected_book_id:
                for field, entry in self.entries.items():
                    entry.delete(0, tk.END)
                    entry.insert(0, book.get(field, ""))

                self.update_button.config(state=tk.NORMAL)
                self.status_bar.config(text=f"Редактирование книги: '{book.get('title', '')}'")
                break

    def clear_form(self):
        """Очистка формы"""
        for entry in self.entries.values():
            entry.delete(0, tk.END)

        self.update_button.config(state=tk.DISABLED)
        self.selected_book_id = None
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

        self.status_bar.config(text="Форма очищена. Готов к вводу новой книги.")

    def on_book_select(self, event):
        """Обработка выбора книги в таблице"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            book_id = int(item["values"][0])
            self.selected_book_id = book_id

            book_title = item["values"][1]
            self.status_bar.config(text=f"Выбрана книга: '{book_title}'")

    def search_books(self):
        """Поиск книг в БД"""
        search_text = self.search_entry.get().strip().lower()
        search_field = self.search_var.get()

        if not search_text:
            messagebox.showwarning("Ошибка", "Введите текст для поиска!")
            return

        found_books = self.search_in_db(search_field, search_text)
        self.update_table(found_books)

        if found_books:
            self.status_bar.config(text=f"Найдено книг: {len(found_books)}")
        else:
            self.status_bar.config(text="Книги по заданным критериям не найдены.")

    def reset_search(self):
        """Сброс результатов поиска"""
        self.search_entry.delete(0, tk.END)
        self.books = self.load_data_from_db()
        self.update_table()
        self.status_bar.config(text="Поиск сброшен. Отображены все книги.")

    def export_data(self):
        """Экспорт данных в файл"""
        if not self.books:
            messagebox.showwarning("Ошибка", "Нет данных для экспорта!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                # Убираем поля created_at и updated_at для экспорта
                export_books = []
                for book in self.books:
                    export_book = {k: v for k, v in book.items() 
                                 if k not in ['created_at', 'updated_at']}
                    export_books.append(export_book)
                
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(export_books, file, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("Успех", f"Данные успешно экспортированы в файл:\n{file_path}")
                self.status_bar.config(text=f"Данные экспортированы в: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать данные: {str(e)}")

    def import_data(self):
        """Импорт данных из файла в БД"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    imported_books = json.load(file)

                if not isinstance(imported_books, list):
                    messagebox.showerror("Ошибка", "Некорректный формат данных в файле!")
                    return

                confirm = messagebox.askyesno(
                    "Подтверждение импорта",
                    f"Найдено {len(imported_books)} записей. Добавить в существующие данные?"
                )

                if confirm:
                    added_count = 0
                    for book in imported_books:
                        # Проверка обязательных полей
                        if 'title' in book and 'author' in book and 'year' in book:
                            # Сохранение в БД
                            book_id = self.save_data_to_db(book, 'insert')
                            if book_id:
                                book['id'] = book_id
                                self.books.append(book)
                                added_count += 1
                    
                    self.update_table()
                    messagebox.showinfo("Успех", f"Успешно импортировано {added_count} записей!")
                    self.status_bar.config(
                        text=f"Импортировано {added_count} записей из: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось импортировать данные: {str(e)}")

    def __del__(self):
        """Закрытие соединения с БД при удалении объекта"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'connection') and self.connection and self.connection.is_connected():
            self.connection.close()
            print("Соединение с базой данных закрыто")


def main():
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()