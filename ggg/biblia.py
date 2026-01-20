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
        self.root.state('zoomed')

         # Инициализация основных атрибутов
        self.config_file = "db_config.ini"
        self.db_config = {}
        self.connection = None
        self.cursor = None
        self.books = []
        self.selected_book_id = None
        self.entries = {}
        
        # Загрузка конфигурации БД
        self.db_config = self.load_db_config()
        
        # Подключение к БД
        self.connection = None
        self.cursor = None
        self.connect_to_db()
        

        if not self.connection or not self.connection.is_connected():
            print("Не удалось подключиться к БД. Работаем в автономном режиме.")
            self.books = []
        else:
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

         # Инициализация фильтров (после создания интерфейса)
        if hasattr(self, 'genre_menu'):
            self.root.after(100, self.update_filter_lists)  # Небольшая задержка   

       # Устанавливаем время последнего обновления
        if hasattr(self, 'last_update_label'):
            self.last_update_label.config(text=f"Обновлено: {datetime.now().strftime('%H:%M:%S')}")
        
    def get_unique_genres(self):
        """Получение уникальных жанров из БД"""
        try:
            query = "SELECT DISTINCT genre FROM books WHERE genre IS NOT NULL AND genre != '' ORDER BY genre"
            self.cursor.execute(query)
            genres = []
            for row in self.cursor.fetchall():
                genre = row['genre']
                if genre and genre.strip():  # Проверяем, что не пустое
                    clean_genre = genre.strip()
                    if clean_genre not in genres:  # Убираем дубликаты
                        genres.append(clean_genre)
            print(f"Получено уникальных жанров: {len(genres)}")
            return genres
        except Error as e:
            print(f"Ошибка при получении жанров: {e}")
            return []

    def get_unique_authors(self):
        """Получение уникальных авторов из БД"""
        try:
            query = "SELECT DISTINCT author FROM books WHERE author IS NOT NULL AND author != '' ORDER BY author"
            self.cursor.execute(query)
            authors = []
            for row in self.cursor.fetchall():
                author = row['author']
                if author and author.strip():  # Проверяем, что не пустое
                    clean_author = author.strip()
                    if clean_author not in authors:  # Убираем дубликаты
                        authors.append(clean_author)
            print(f"Получено уникальных авторов: {len(authors)}")
            return authors
        except Error as e:
            print(f"Ошибка при получении авторов: {e}")
            return []

    def get_unique_years(self):
        """Получение уникальных годов издания из БД"""
        try:
            query = "SELECT DISTINCT year FROM books WHERE year IS NOT NULL ORDER BY year DESC"
            self.cursor.execute(query)
            years = []
            for row in self.cursor.fetchall():
                year = row['year']
                if year:
                    year_str = str(year).strip()
                    if year_str not in years:  # Убираем дубликаты
                        years.append(year_str)
            print(f"Получено уникальных годов: {len(years)}")
            return years
        except Error as e:
            print(f"Ошибка при получении годов: {e}")
            return []

    def load_db_config(self):
        """Загрузка конфигурации базы данных"""
        config = configparser.ConfigParser()
        
        # Значения по умолчанию
        default_config = {
            'database': {
                'host': 'localhost',
                'user': 'root',
                'password': 'vada/228',
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
                return True
            else:
                print("Не удалось подключиться к базе данных")
                return False
                
        except Error as e:
            print(f"Ошибка подключения к базе данных: {e}")
            messagebox.showerror(
                "Ошибка подключения", 
                f"Не удалось подключиться к базе данных.\nОшибка: {e}\n\n"
                f"Проверьте настройки подключения в файле {self.config_file}"
            )
            
            # Создаем пустые атрибуты, чтобы избежать ошибок
            self.connection = None
            self.cursor = None
            return False

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
        
        def save_and_reconnect():
            """Сохранение настроек и переподключение"""
            for field_name, entry in entries.items():
                self.db_config[field_name] = entry.get()
            
            # Сохраняем конфигурацию
            config = configparser.ConfigParser()
            config['database'] = self.db_config
            
            with open(self.config_file, 'w') as configfile:
                config.write(configfile)
            
            # Закрываем старое соединение если есть
            if self.cursor:
                self.cursor.close()
            if self.connection and self.connection.is_connected():
                self.connection.close()
            
            # Пытаемся подключиться снова
            if self.connect_to_db():
                if self.connection and self.connection.is_connected():
                    # Инициализируем БД
                    self.init_database()
                    # Перезагружаем данные
                    self.books = self.load_data_from_db()
                    # Обновляем таблицу
                    self.update_table()
                    # Обновляем фильтры
                    self.update_filter_lists()
                    
                    messagebox.showinfo("Успех", "Подключение восстановлено! Данные обновлены.")
                else:
                    messagebox.showwarning("Предупреждение", 
                                         "Настройки сохранены, но подключиться не удалось. "
                                         "Проверьте параметры подключения.")
            else:
                messagebox.showwarning("Предупреждение", 
                                     "Не удалось подключиться с новыми настройками.")
            
            config_window.destroy()
        
        tk.Button(config_window, text="Сохранить и переподключиться", 
                 command=save_and_reconnect, 
                 bg="#3498db", fg="white", padx=20, pady=5).pack(pady=20)

    def init_database(self):
        """Инициализация таблиц в базе данных"""
        # Проверяем подключение
        if not self.connection or not self.connection.is_connected():
            print("Нет подключения к БД. Пропускаем инициализацию таблицы.")
            return
        
        try:
            # Проверяем существование колонок
            self.cursor.execute("SHOW COLUMNS FROM books LIKE 'location'")
            has_location = self.cursor.fetchone()
            
            self.cursor.execute("SHOW COLUMNS FROM books LIKE 'shelf'")
            has_shelf = self.cursor.fetchone()
            
            self.cursor.execute("SHOW COLUMNS FROM books LIKE 'rack'")
            has_rack = self.cursor.fetchone()
            
            # Если есть старые колонки, нужно обновить структуру
            if has_location and (not has_shelf or not has_rack):
                print("Обновляем структуру таблицы...")
                
                # Добавляем новые колонки если их нет
                if not has_shelf:
                    self.cursor.execute("ALTER TABLE books ADD COLUMN shelf VARCHAR(10) DEFAULT ''")
                    print("Добавлена колонка 'shelf'")
                
                if not has_rack:
                    self.cursor.execute("ALTER TABLE books ADD COLUMN rack VARCHAR(10) DEFAULT ''")
                    print("Добавлена колонка 'rack'")
                
                # Переносим данные из location в новые колонки
                self.cursor.execute("""
                    UPDATE books 
                    SET rack = SUBSTRING_INDEX(location, '-', 1),
                        shelf = SUBSTRING_INDEX(location, '-', -1)
                    WHERE location LIKE '%-%'
                """)
                
                # Удаляем старую колонку location
                self.cursor.execute("ALTER TABLE books DROP COLUMN location")
                print("Удалена колонка 'location'")
                
                self.connection.commit()
                print("Структура таблицы обновлена")
            
            # Создаем таблицу если её нет
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
                rack VARCHAR(10) DEFAULT '',
                shelf VARCHAR(10) DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            self.cursor.execute(create_table_query)
            self.connection.commit()
            print("Таблица 'books' создана или уже существует")
            
        except Error as e:
            print(f"Ошибка при инициализации БД: {e}")

    def check_database_data(self):    
        """Проверка содержимого базы данных"""
        print("\n" + "="*50)
        print("ПРОВЕРКА ДАННЫХ В БАЗЕ ДАННЫХ")
        
        try:
            # 1. Все книги
            self.cursor.execute("SELECT COUNT(*) as count FROM books")
            total = self.cursor.fetchone()['count']
            print(f"Всего книг в БД: {total}")
            
            # 2. Несколько примеров книг
            self.cursor.execute("SELECT title, author, genre, year FROM books LIMIT 10")
            books = self.cursor.fetchall()
            print(f"\nПервые {len(books)} книг в БД:")
            for i, book in enumerate(books, 1):
                print(f"  {i}. '{book['title']}' - {book['author']} ({book['year']}), жанр: {book['genre']}")
            
            # 3. Уникальные жанры
            self.cursor.execute("SELECT DISTINCT genre FROM books WHERE genre IS NOT NULL AND genre != ''")
            genres = [row['genre'] for row in self.cursor.fetchall()]
            print(f"\nУникальные жанры ({len(genres)}): {genres}")
            
            # 4. Уникальные авторы
            self.cursor.execute("SELECT DISTINCT author FROM books WHERE author IS NOT NULL AND author != ''")
            authors = [row['author'] for row in self.cursor.fetchall()]
            print(f"\nУникальные авторы ({len(authors)}): {authors[:10]}{'...' if len(authors) > 10 else ''}")
            
            # 5. Уникальные годы
            self.cursor.execute("SELECT DISTINCT year FROM books WHERE year IS NOT NULL")
            years = [row['year'] for row in self.cursor.fetchall()]
            print(f"\nУникальные годы ({len(years)}): {years}")
            
            print("="*50 + "\n")
            
        except Error as e:
            print(f"Ошибка при проверке БД: {e}")

    def load_data_from_db(self):
        """Загрузка данных из базы данных"""
        # Проверяем, есть ли подключение
        if not self.connection or not self.connection.is_connected():
            print("Нет подключения к БД. Возвращаем пустой список.")
            return []
        
        try:
            query = "SELECT * FROM books ORDER BY rack, shelf, title"
            self.cursor.execute(query)
            books = self.cursor.fetchall()
            
            # Преобразование в список словарей
            result = []
            for i, book in enumerate(books, start=1):
                book_dict = {}
                for key, value in book.items():
                    if key == 'id':
                        book_dict[key] = i
                    elif hasattr(value, 'isoformat'):
                        book_dict[key] = value.isoformat()
                    else:
                        book_dict[key] = str(value) if value is not None else ""
                result.append(book_dict)
            
            print(f"Загружено книг из БД: {len(result)}")
            return result
            
        except Error as e:
            print(f"Ошибка при загрузке данных: {e}")
            return []

    def save_data_to_db(self, book_data, operation='insert'):
        """Сохранение данных в базу данных"""
        # Проверяем подключение
        if not self.connection or not self.connection.is_connected():
            print("Нет подключения к БД. Данные не сохранены.")
            return None
        
        try:
            if operation == 'insert':
                query = """
                INSERT INTO books (title, author, year, genre, publisher, isbn, quantity, rack, shelf)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    book_data['title'],
                    book_data['author'],
                    book_data['year'],
                    book_data.get('genre', ''),
                    book_data.get('publisher', ''),
                    book_data.get('isbn', ''),
                    book_data.get('quantity', 1),
                    book_data.get('rack', ''),
                    book_data.get('shelf', '')
                )
                self.cursor.execute(query, values)
                book_id = self.cursor.lastrowid
                
            elif operation == 'update':
                query = """
                UPDATE books 
                SET title = %s, author = %s, year = %s, genre = %s, 
                    publisher = %s, isbn = %s, quantity = %s, rack = %s, shelf = %s
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
                    book_data.get('rack', ''),
                    book_data.get('shelf', ''),
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
        """Удаление книги из базы данных и перенумерация ID"""
         # Проверяем подключение
        if not self.connection or not self.connection.is_connected():
            print("Нет подключения к БД. Удаление невозможно.")
            return False

        try:
            # Удаляем книгу
            query = "DELETE FROM books WHERE id = %s"
            self.cursor.execute(query, (book_id,))
            
            # Получаем оставшиеся книги, отсортированные по id
            select_query = "SELECT id FROM books ORDER BY id"
            self.cursor.execute(select_query)
            remaining_books = self.cursor.fetchall()
            
            # Перенумерация оставшихся книг
            for new_id, book in enumerate(remaining_books, start=1):
                old_id = book['id']
                if old_id != new_id:
                    update_query = "UPDATE books SET id = %s WHERE id = %s"
                    self.cursor.execute(update_query, (new_id, old_id))
            
            # Сбрасываем автоинкремент
            reset_query = "ALTER TABLE books AUTO_INCREMENT = 1"
            self.cursor.execute(reset_query)
            
            self.connection.commit()
            return True
            
        except Error as e:
            print(f"Ошибка при удалении данных: {e}")
            self.connection.rollback()
            return False

    def search_in_db(self, field, value):
        """Поиск книг в базе данных"""
        # Проверяем подключение
        if not self.connection or not self.connection.is_connected():
            print("Нет подключения к БД. Поиск невозможен.")
            return []

        try:
            # Безопасное формирование запроса
            allowed_fields = ['title', 'author', 'genre', 'isbn', 'year']
            if field not in allowed_fields:
                field = 'title'
            
            query = f"SELECT * FROM books WHERE {field} LIKE %s ORDER BY id"
            self.cursor.execute(query, (f"%{value}%",))
            books = self.cursor.fetchall()
            
            # Преобразование в список словарей с перенумерацией
            result = []
            for i, book in enumerate(books, start=1):
                book_dict = {}
                for key, value in book.items():
                    if key == 'id':
                        book_dict[key] = i  # Перенумеровываем ID
                    elif hasattr(value, 'isoformat'):
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

    def create_data_tab(self):
        """Создание вкладки 'Данные книги'"""
        # Основной контейнер
        main_form = tk.Frame(self.data_tab, bg=self.bg_color)
        main_form.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Поля ввода - КОРРЕКТНОЕ ОПРЕДЕЛЕНИЕ
        fields = [
            # (метка, имя_поля, тип_поля)
            ("Название книги:", "title", "entry"),
            ("Автор:", "author", "entry"),
            ("Год издания:", "year", "entry"),
            ("Жанр:", "genre", "entry"),
            ("Издательство:", "publisher", "entry"),
            ("ISBN:", "isbn", "entry"),
            ("Количество:", "quantity", "entry"),
            ("Стеллаж:", "rack", "combobox"),
            ("Полка:", "shelf", "combobox")
        ]

        self.entries = {}
        for i, (label_text, field_name, field_type) in enumerate(fields):
            # Каждая строка в отдельном фрейме
            row = tk.Frame(main_form, bg=self.bg_color)
            row.pack(fill=tk.X, pady=8)
            
            # Метка слева
            tk.Label(
                row,
                text=label_text,
                font=("Arial", 11),
                bg=self.bg_color,
                fg=self.accent_color,
                width=18,
                anchor="w"
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            # Разные типы полей
            if field_type == "combobox":
                if field_name == "rack":
                    # Стеллаж - буквы A-Z
                    values = ["", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", 
                             "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", 
                             "V", "W", "X", "Y", "Z"]
                    combobox = ttk.Combobox(
                        row,
                        values=values,
                        state="normal",
                        font=("Arial", 11),
                        width=8
                    )
                    combobox.pack(side=tk.LEFT)
                    self.entries[field_name] = combobox
                    
                elif field_name == "shelf":
                    # Полка - цифры 1-20
                    values = [""] + [str(i) for i in range(1, 21)]
                    combobox = ttk.Combobox(
                        row,
                        values=values,
                        state="normal",
                        font=("Arial", 11),
                        width=8
                    )
                    combobox.pack(side=tk.LEFT)
                    self.entries[field_name] = combobox
            else:
                # Обычное текстовое поле
                entry = tk.Entry(
                    row,
                    font=("Arial", 11),
                    width=25,
                    relief=tk.GROOVE,
                    borderwidth=1
                )
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.entries[field_name] = entry

        # Кнопки в центре
        btn_container = tk.Frame(main_form, bg=self.bg_color)
        btn_container.pack(fill=tk.X, pady=(30, 0))
        
        # Центрирующий фрейм
        center_buttons = tk.Frame(btn_container, bg=self.bg_color)
        center_buttons.pack(expand=True)

        # Кнопка добавления
        self.add_button = tk.Button(
            center_buttons,
            text="➕ Добавить \n книгу",
            command=self.add_book,
            bg="#2ecc71",
            fg="white",
            font=("Arial", 11, "bold"),
            width=20,
            height=1,
            cursor="hand2",
            padx=1,
            pady=8
        )
        self.add_button.pack(side=tk.LEFT, padx=1)

        # Кнопка очистки
        self.clear_button = tk.Button(
            center_buttons,
            text="🗑️ Очистить \n форму",
            command=self.clear_form,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 11, "bold"),
            width=20,
            height=1,
            cursor="hand2",
            padx=10,
            pady=8
        )
        self.clear_button.pack(side=tk.LEFT, padx=10)

    def create_search_tab(self):
        """Создание вкладки 'Поиск и фильтры'"""
        # Основной контейнер
        search_main = tk.Frame(self.search_tab, bg=self.bg_color)
        search_main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 1. Поиск по ISBN
        tk.Label(
            search_main,
            text="🔎 Поиск по ISBN:",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.accent_color
        ).pack(anchor="w", pady=(0, 10))

        isbn_row = tk.Frame(search_main, bg=self.bg_color)
        isbn_row.pack(fill=tk.X, pady=(0, 20))

        self.isbn_entry = tk.Entry(
            isbn_row,
            font=("Arial", 11),
            width=25,
            relief=tk.GROOVE,
            borderwidth=1
        )
        self.isbn_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        tk.Button(
            isbn_row,
            text="Найти",
            command=self.search_by_isbn,
            bg=self.button_color,
            fg="white",
            font=("Arial", 10, "bold"),
            width=10,
            padx=5
        ).pack(side=tk.RIGHT)

        # 2. Фильтры по категориям
        tk.Label(
            search_main,
            text="🎯 Фильтры по категориям:",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.accent_color
        ).pack(anchor="w", pady=(0, 10))

        # Фильтр по жанру
        genre_row = tk.Frame(search_main, bg=self.bg_color)
        genre_row.pack(fill=tk.X, pady=5)

        tk.Label(
            genre_row,
            text="Жанр:",
            font=("Arial", 11),
            bg=self.bg_color,
            fg=self.fg_color,
            width=10,
            anchor="w"
        ).pack(side=tk.LEFT)

        self.genre_var = tk.StringVar()
        self.genre_var.set("Выберите жанр")
  
        genres = ["Выберите жанр"] + self.get_unique_genres()
        self.genre_menu = ttk.Combobox(
            genre_row,
            textvariable=self.genre_var,
            values=genres,
            state="readonly",
            font=("Arial", 10),
            width=25
        )
        self.genre_menu.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        tk.Button(
            genre_row,
            text="×",
            command=lambda: self.genre_var.set("Выберите жанр"),
            bg="#e74c3c",
            fg="white",
            font=("Arial", 9, "bold"),
            width=3
        ).pack(side=tk.RIGHT)

        # Фильтр по автору
        author_row = tk.Frame(search_main, bg=self.bg_color)
        author_row.pack(fill=tk.X, pady=5)

        tk.Label(
            author_row,
            text="Автор:",
            font=("Arial", 11),
            bg=self.bg_color,
            fg=self.fg_color,
            width=10,
            anchor="w"
        ).pack(side=tk.LEFT)

        self.author_var = tk.StringVar()
        self.author_var.set("Выберите автора")
        
        authors = ["Выберите автора"] + sorted(self.get_unique_authors())
        self.author_menu = ttk.Combobox(
            author_row,
            textvariable=self.author_var,
            values=authors,
            state="readonly",
            font=("Arial", 10),
            width=25
        )
        self.author_menu.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        tk.Button(
            author_row,
            text="×",
            command=lambda: self.author_var.set("Выберите автора"),
            bg="#e74c3c",
            fg="white",
            font=("Arial", 9, "bold"),
            width=3
        ).pack(side=tk.RIGHT)

        # Фильтр по году
        year_row = tk.Frame(search_main, bg=self.bg_color)
        year_row.pack(fill=tk.X, pady=5)

        tk.Label(
            year_row,
            text="Год:",
            font=("Arial", 11),
            bg=self.bg_color,
            fg=self.fg_color,
            width=10,
            anchor="w"
        ).pack(side=tk.LEFT)

        self.year_var = tk.StringVar()
        self.year_var.set("Выберите год")
        
        years = ["Выберите год"] + sorted(self.get_unique_years(), reverse=True)
        self.year_menu = ttk.Combobox(
            year_row,
            textvariable=self.year_var,
            values=years,
            state="readonly",
            font=("Arial", 10),
            width=25
        )
        self.year_menu.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        tk.Button(
            year_row,
            text="×",
            command=lambda: self.year_var.set("Выберите год"),
            bg="#e74c3c",
            fg="white",
            font=("Arial", 9, "bold"),
            width=3
        ).pack(side=tk.RIGHT)

         # Фильтр по стеллажу
        rack_row = tk.Frame(search_main, bg=self.bg_color)
        rack_row.pack(fill=tk.X, pady=5)

        tk.Label(
            rack_row,
            text="Стеллаж:",
            font=("Arial", 11),
            bg=self.bg_color,
            fg=self.fg_color,
            width=10,
            anchor="w"
        ).pack(side=tk.LEFT)

        self.rack_var = tk.StringVar()
        self.rack_var.set("Выберите стеллаж")
        
        racks = ["Выберите стеллаж"] + sorted(self.get_unique_racks())
        self.rack_menu = ttk.Combobox(
            rack_row,
            textvariable=self.rack_var,
            values=racks,
            state="readonly",
            font=("Arial", 10),
            width=25
        )
        self.rack_menu.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        tk.Button(
            rack_row,
            text="×",
            command=lambda: self.rack_var.set("Выберите стеллаж"),
            bg="#e74c3c",
            fg="white",
            font=("Arial", 9, "bold"),
            width=3
        ).pack(side=tk.RIGHT)
        
        # Получаем уникальные стеллажи из БД
        racks = ["Выберите стеллаж"] + sorted(self.get_unique_racks())
        self.rack_menu = ttk.Combobox(
            rack_row,
            textvariable=self.rack_var,
            values=racks,
            state="readonly",
            font=("Arial", 10),
            width=25
        )
        self.rack_menu.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        tk.Button(
            rack_row,
            text="×",
            command=lambda: self.rack_var.set("Выберите стеллаж"),
            bg="#e74c3c",
            fg="white",
            font=("Arial", 9, "bold"),
            width=3
        ).pack(side=tk.RIGHT)

        # Кнопка применения фильтра
        filter_button_row = tk.Frame(search_main, bg=self.bg_color)
        filter_button_row.pack(fill=tk.X, pady=(15, 10))
        
        tk.Button(
            filter_button_row,
            text="🔍 Применить фильтр",
            command=self.apply_combined_filter,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 11, "bold"),
            width=20,
            padx=10,
            pady=8
        ).pack()

        # Кнопки управления
        control_frame = tk.Frame(search_main, bg=self.bg_color)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(
            control_frame,
            text="📚 Показать все",
            command=self.show_all_books,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            padx=5
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            control_frame,
            text="🗑️ Очистить все",
            command=self.clear_filters,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            padx=5
        ).pack(side=tk.RIGHT)

    def create_actions_tab(self):
        """Создание вкладки 'Действия'"""
        # Основной контейнер
        actions_main = tk.Frame(self.actions_tab, bg=self.bg_color)
        actions_main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Кнопки действий
        tk.Button(
            actions_main,
            text="🔄 Обновить каталог",
            command=self.refresh_catalog,
            bg="#3498db",
            fg="white",
            font=("Arial", 11, "bold"),
            width=25,
            height=1,
            cursor="hand2",
            pady=10
        ).pack(pady=10)

        tk.Button(
            actions_main,
            text="✏️ Редактировать книгу",
            command=self.edit_book,
            bg="#f39c12",
            fg="white",
            font=("Arial", 11, "bold"),
            width=25,
            height=1,
            cursor="hand2",
            pady=10
        ).pack(pady=10)

        tk.Button(
            actions_main,
            text="🗑️ Удалить книгу",
            command=self.delete_book,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 11, "bold"),
            width=25,
            height=1,
            cursor="hand2",
            pady=10
        ).pack(pady=10)

        tk.Button(
            actions_main,
            text="📥 Импорт данных",
            command=self.import_data,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 11, "bold"),
            width=25,
            height=1,
            cursor="hand2",
            pady=10
        ).pack(pady=10)

        tk.Button(
            actions_main,
            text="📤 Экспорт данных",
            command=self.export_data,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            width=25,
            height=1,
            cursor="hand2",
            pady=10
        ).pack(pady=10)

        # Разделитель
        separator = tk.Frame(actions_main, height=2, bg=self.accent_color)
        separator.pack(fill=tk.X, pady=20)

        # Статистика
        tk.Label(
            actions_main,
            text="📊 Статистика:",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.accent_color
        ).pack(anchor="w", pady=(0, 10))

        self.stats_label_tab = tk.Label(
            actions_main,
            text="Всего книг: 0",
            font=("Arial", 11),
            bg=self.bg_color,
            fg=self.fg_color
        )
        self.stats_label_tab.pack(anchor="w")

        self.last_update_label_tab = tk.Label(
            actions_main,
            text="Обновлено: --:--:--",
            font=("Arial", 10),
            bg=self.bg_color,
            fg="#7f8c8d"
        )
        self.last_update_label_tab.pack(anchor="w", pady=(5, 0))

    def create_catalog_tab(self, parent):
        """Создание каталога книг в правой панели"""
        # Фрейм для каталога
        catalog_frame = tk.Frame(parent, bg=self.bg_color)
        catalog_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Заголовок каталога
        header_frame = tk.Frame(catalog_frame, bg=self.accent_color)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            header_frame,
            text="📚 КАТАЛОГ КНИГ",
            font=("Arial", 14, "bold"),
            bg=self.accent_color,
            fg="white",
            padx=10,
            pady=8
        ).pack()

        # Статистика над таблицей
        stats_frame = tk.Frame(catalog_frame, bg=self.bg_color)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        self.stats_label = tk.Label(
            stats_frame,
            text="Всего книг: 0",
            font=("Arial", 11, "bold"),
            bg=self.bg_color,
            fg=self.accent_color
        )
        self.stats_label.pack(side=tk.LEFT)

        self.last_update_label = tk.Label(
            stats_frame,
            text="Обновлено: --:--:--",
            font=("Arial", 10),
            bg=self.bg_color,
            fg="#7f8c8d"
        )
        self.last_update_label.pack(side=tk.RIGHT)

        # Таблица с книгами
        table_container = tk.Frame(catalog_frame, bg=self.bg_color)
        table_container.pack(fill=tk.BOTH, expand=True)

        columns = ("ID", "Название", "Автор", "Год", "Жанр", "Издательство", "ISBN", "Кол-во", "Стеллаж", "Полка")

        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            height=25,
            selectmode="browse"
        )

        # Настраиваем ширину колонок
        column_widths = [40, 230, 140, 60, 110, 140, 110, 60, 70, 60]
        for col, width in zip(columns, column_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, minwidth=40)

        # Горизонтальный скроллбар
        h_scrollbar = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=h_scrollbar.set)

        # Размещаем таблицу и скроллбар
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Привязываем события
        self.tree.bind("<MouseWheel>", self.on_mousewheel)
        self.tree.bind("<<TreeviewSelect>>", self.on_book_select)

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

        # Основной контейнер - на весь экран
        main_container = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.bg_color, sashwidth=5, sashrelief=tk.RAISED)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ЛЕВАЯ ПАНЕЛЬ - ВКЛАДКИ (30% ширины)
        left_panel = tk.Frame(main_container, bg=self.bg_color, width=380)
        
        # Создаем Notebook для вкладок слева
        self.tab_control = ttk.Notebook(left_panel)
        self.tab_control.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Вкладка 1: Данные книги
        self.data_tab = tk.Frame(self.tab_control, bg=self.bg_color)
        self.tab_control.add(self.data_tab, text="📖 Данные \n книги")
        
        # Вкладка 2: Поиск и фильтры
        self.search_tab = tk.Frame(self.tab_control, bg=self.bg_color)
        self.tab_control.add(self.search_tab, text="🔍 Поиск и \n фильтры")

        # Вкладка 3: Действия
        self.actions_tab = tk.Frame(self.tab_control, bg=self.bg_color)
        self.tab_control.add(self.actions_tab, text="⚡ Действия \n")

        # ПРАВАЯ ПАНЕЛЬ - КАТАЛОГ КНИГ (70% ширины)
        right_panel = tk.Frame(main_container, bg=self.bg_color)

        # Добавляем панели в PanedWindow
        main_container.add(left_panel, minsize=330, width=380)
        main_container.add(right_panel, minsize=600)

        # Создаем содержимое вкладок слева
        self.create_data_tab()
        self.create_search_tab()
        self.create_actions_tab()
        
        # Создаем каталог книг справа
        self.create_catalog_tab(right_panel)

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
        
    def on_resize(event):
            # Обновляем ширину левой панели
            screen_width = self.root.winfo_width()
            left_panel.config(width=int(screen_width * 0.3))
            
            # Обновляем размер шрифта таблицы
            if screen_width < 1400:
                font_size = 9
            elif screen_width < 1600:
                font_size = 10
            else:
                font_size = 11
                
            style = ttk.Style()
            style.configure("Treeview", font=("Arial", font_size))
            style.configure("Treeview.Heading", font=("Arial", font_size, "bold"))
        
        # Привязываем обработчик изменения размера
            self.root.bind('<Configure>', on_resize)

    def setup_styles(self):
        """Настройка стилей приложения"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Цвета
        self.bg_color = "#f8f9fa"  # Светлее фон
        self.fg_color = "#2c3e50"  # Темнее текст
        self.accent_color = "#3498db"  # Акцентный синий
        self.button_color = "#3498db"
        self.delete_color = "#e74c3c"
        self.edit_color = "#f39c12"
        
        # Настройка окна
        self.root.configure(bg=self.bg_color)
        
        # Стиль вкладок
        self.style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        self.style.configure("TNotebook.Tab", 
                           font=("Arial", 11, "bold"),
                           padding=[20, 8],
                           background="#e9ecef")
        self.style.map("TNotebook.Tab", 
                      background=[("selected", self.accent_color)],
                      foreground=[("selected", "white")])
        
        # Настройка стиля таблицы
        self.style.configure("Treeview", 
                           font=("Arial", 10),
                           background="white",
                           fieldbackground="white",
                           rowheight=25)
        self.style.configure("Treeview.Heading", 
                           font=("Arial", 10, "bold"),
                           background=self.accent_color,
                           foreground="white")
        self.style.map("Treeview.Heading", 
                      background=[("active", "#3498db")])
        
        # Настройка скроллбаров
        self.style.configure("Vertical.TScrollbar", 
                           background="#bdc3c7",
                           arrowcolor=self.accent_color,
                           troughcolor="#ecf0f1")
        self.style.configure("Horizontal.TScrollbar", 
                           background="#bdc3c7",
                           arrowcolor=self.accent_color,
                           troughcolor="#ecf0f1")

    def search_by_isbn(self):
        """Поиск книги по ISBN"""
        isbn_text = self.isbn_entry.get().strip()
        
        if not isbn_text:
            messagebox.showwarning("Ошибка", "Введите ISBN для поиска!")
            return
        
        try:
            query = "SELECT * FROM books WHERE isbn LIKE %s ORDER BY title"
            self.cursor.execute(query, (f"%{isbn_text}%",))
            
            books = self.cursor.fetchall()
            
            result = []
            for i, book in enumerate(books, start=1):
                book_dict = {}
                for key, value in book.items():
                    if key == 'id':
                        book_dict[key] = i
                    elif hasattr(value, 'isoformat'):
                        book_dict[key] = value.isoformat()
                    else:
                        book_dict[key] = str(value) if value is not None else ""
                result.append(book_dict)
            
            self.update_table(result)
            
            if result:
                self.status_bar.config(text=f"Найдено книг по ISBN: {len(result)}")
                # Переключаем на первую вкладку, чтобы видеть результаты
                self.tab_control.select(0)
            else:
                self.status_bar.config(text="Книги с таким ISBN не найдены.")
                
        except Error as e:
            print(f"Ошибка при поиске по ISBN: {e}")
            messagebox.showerror("Ошибка", f"Не удалось выполнить поиск: {str(e)}")

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
                book.get("rack", ""),
                book.get("shelf", "")
            )
            self.tree.insert("", tk.END, values=values)

        # Обновляем статистику везде
        total_books = len(books)
        current_time = datetime.now().strftime("%H:%M:%S")
        
        self.stats_label.config(text=f"Всего книг: {total_books}")
        self.last_update_label.config(text=f"Обновлено: {current_time}")
        
        if hasattr(self, 'stats_label_tab'):
            self.stats_label_tab.config(text=f"Всего книг: {total_books}")
        if hasattr(self, 'last_update_label_tab'):
            self.last_update_label_tab.config(text=f"Обновлено: {current_time}")
            
        self.status_bar.config(text=f"Готово. Загружено книг: {total_books} | Время: {current_time}")

    def add_book(self):
        """Добавление новой книги в БД"""
        book_data = {}
        for field, widget in self.entries.items():
            if isinstance(widget, ttk.Combobox):
                value = widget.get().strip()
            else:
                value = widget.get().strip()
            
            # Проверка обязательных полей
            if field in ['title', 'author', 'year'] and not value:
                messagebox.showwarning("Ошибка", f"Поле '{field}' не может быть пустым!")
                if isinstance(widget, ttk.Combobox):
                    widget.focus_set()
                else:
                    widget.focus_set()
                return
            
            # Специальная обработка для стеллажа и полки
            if field == 'rack':
                # Проверяем, что стеллаж - это буква
                if value and not value.isalpha():
                    messagebox.showwarning("Ошибка", "Стеллаж должен содержать только буквы!")
                    widget.focus_set()
                    return
                # Приводим к верхнему регистру
                value = value.upper()
                
            elif field == 'shelf':
                # Проверяем, что полка - это цифры
                if value and not value.isdigit():
                    messagebox.showwarning("Ошибка", "Полка должна содержать только цифры!")
                    widget.focus_set()
                    return
            
            book_data[field] = value

        # Валидация года
        try:
            year = int(book_data["year"])
            current_year = datetime.now().year
            if year < 1000 or year > current_year + 1:
                messagebox.showwarning("Ошибка", f"Укажите корректный год издания (1000-{current_year + 1})!")
                self.entries["year"].focus_set()
                return
        except ValueError:
            messagebox.showwarning("Ошибка", "Год издания должен быть числом!")
            self.entries["year"].focus_set()
            return

        # Валидация количества
        try:
            quantity = int(book_data.get("quantity", 1))
            if quantity < 1:
                messagebox.showwarning("Ошибка", "Количество должно быть положительным числом!")
                self.entries["quantity"].focus_set()
                return
        except ValueError:
            messagebox.showwarning("Ошибка", "Количество должно быть числом!")
            self.entries["quantity"].focus_set()
            return

        # Сохранение в БД
        book_id = self.save_data_to_db(book_data, 'insert')
        
        if book_id:
            book_data["id"] = book_id
            self.books.append(book_data)
            self.update_table()
            self.clear_form()
            self.status_bar.config(text=f"Книга '{book_data['title']}' успешно добавлена в БД!")
            
            # Обновляем списки фильтров
            self.update_filter_lists()
            
            # Прокручиваем к новой книге
            if self.tree.get_children():
                self.tree.see(self.tree.get_children()[-1])
        else:
            messagebox.showerror("Ошибка", "Не удалось добавить книгу в базу данных!")

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
        """Редактирование выбранной книги в отдельном окне"""
        if self.selected_book_id is None:
            messagebox.showwarning("Ошибка", "Выберите книгу для редактирования!")
            return

        # Найти выбранную книгу
        selected_book = None
        for book in self.books:
            if book.get("id") == self.selected_book_id:
                selected_book = book
                break
        
        if not selected_book:
            messagebox.showwarning("Ошибка", "Книга не найдена!")
            return
        
        # Создать окно редактирования
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Редактирование книги: {selected_book.get('title', '')}")
        edit_window.geometry("500x650")
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # Заголовок
        tk.Label(edit_window, text=f"Редактирование книги", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        tk.Label(edit_window, text=f"ID: {selected_book.get('id', '')}", 
                 font=("Arial", 10)).pack(pady=5)
        
        # Поля для редактирования
        fields = [
            ("Название:", "title"),
            ("Автор:", "author"),
            ("Год издания:", "year"),
            ("Жанр:", "genre"),
            ("Издательство:", "publisher"),
            ("ISBN:", "isbn"),
            ("Количество экземпляров:", "quantity"),
            ("Стеллаж (буква):", "rack"),
            ("Полка (цифра):", "shelf")
        ]
        
        edit_entries = {}
        for i, (label_text, field_name) in enumerate(fields):
            frame = tk.Frame(edit_window)
            frame.pack(fill=tk.X, padx=20, pady=5)
            
            tk.Label(frame, text=label_text, width=25, anchor="w").pack(side=tk.LEFT)
            
            entry = tk.Entry(frame, width=30)
            entry.pack(side=tk.RIGHT, padx=10)
            
            # Заполнить текущими значениями
            entry.insert(0, selected_book.get(field_name, ""))
            edit_entries[field_name] = entry
        
        def save_edited_book():
            """Сохранение отредактированной книги"""
            book_data = {}
            for field, entry in edit_entries.items():
                value = entry.get().strip()
                
                # Проверка обязательных полей
                if field in ['title', 'author', 'year'] and not value:
                    messagebox.showwarning("Ошибка", f"Поле '{field}' не может быть пустым!")
                    return
                
                # Валидация стеллажа
                if field == 'rack' and value:
                    if not value.replace(' ', '').isalpha():
                        messagebox.showwarning("Ошибка", "Стеллаж должен содержать только буквы!")
                        return
                    value = value.upper()
                
                # Валидация полки
                if field == 'shelf' and value:
                    if not value.replace(' ', '').isdigit():
                        messagebox.showwarning("Ошибка", "Полка должна содержать только цифры!")
                        return
                
                book_data[field] = value
            
            # Валидация года
            try:
                year = int(book_data["year"])
                current_year = datetime.now().year
                if year < 1000 or year > current_year + 1:
                    messagebox.showwarning("Ошибка", f"Укажите корректный год издания (1000-{current_year + 1})!")
                    return
            except ValueError:
                messagebox.showwarning("Ошибка", "Год издания должен быть числом!")
                return
            
            # Валидация количества
            try:
                quantity = int(book_data.get("quantity", 1))
                if quantity < 1:
                    messagebox.showwarning("Ошибка", "Количество должно быть положительным числом!")
                    return
            except ValueError:
                messagebox.showwarning("Ошибка", "Количество должно быть числом!")
                return
            
            # Обновление в БД
            if self.save_data_to_db(book_data, 'update'):
                # Обновление в локальном списке
                for i, book in enumerate(self.books):
                    if book.get("id") == self.selected_book_id:
                        book_data["id"] = self.selected_book_id
                        self.books[i] = book_data
                        break
                
                self.update_table()
                edit_window.destroy()
                self.clear_form()
                messagebox.showinfo("Успех", "Книга успешно обновлена!")
                self.status_bar.config(text=f"Книга '{book_data['title']}' успешно обновлена")
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить книгу в базе данных!")
        
        # Кнопки
        button_frame = tk.Frame(edit_window)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Сохранить", command=save_edited_book,
                 bg="#2ecc71", fg="white", padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="Отмена", command=edit_window.destroy,
                 bg="#95a5a6", fg="white", padx=20, pady=8).pack(side=tk.LEFT, padx=10)

    def clear_form(self):
        """Очистка формы"""
        for field, widget in self.entries.items():
            if isinstance(widget, ttk.Combobox):
                widget.set("")
            else:
                widget.delete(0, tk.END)

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

    def filter_by_genre(self, selected_genre):
        """Фильтрация по выбранному жанру"""
        if selected_genre == "Выберите жанр":
            return
        
        try:
            query = "SELECT * FROM books WHERE genre = %s ORDER BY title"
            self.cursor.execute(query, (selected_genre,))
            books = self.cursor.fetchall()
            
            result = []
            for i, book in enumerate(books, start=1):
                book_dict = {}
                for key, value in book.items():
                    if key == 'id':
                        book_dict[key] = i
                    elif hasattr(value, 'isoformat'):
                        book_dict[key] = value.isoformat()
                    else:
                        book_dict[key] = str(value) if value is not None else ""
                result.append(book_dict)
            
            self.update_table(result)
            self.status_bar.config(text=f"Найдено книг в жанре '{selected_genre}': {len(result)}")
            
        except Error as e:
            print(f"Ошибка при фильтрации по жанру: {e}")
            messagebox.showerror("Ошибка", f"Не удалось применить фильтр: {str(e)}")

    def apply_combined_filter(self):
        """Применение комбинированного фильтра по всем выбранным критериям"""
        print("\n" + "="*50)
        print("НАЧАЛО ФИЛЬТРАЦИИ")
        
        genre = self.genre_var.get()
        author = self.author_var.get()
        year = self.year_var.get()
        rack = self.rack_var.get()  # Добавляем стеллаж
        
        print(f"Выбранные критерии:")
        print(f"  Жанр: '{genre}'")
        print(f"  Автор: '{author}'")
        print(f"  Год: '{year}'")
        print(f"  Стеллаж: '{rack}'")
        
        # Проверяем, что выбрано хотя бы одно значение
        if (genre == "Выберите жанр" and 
            author == "Выберите автора" and 
            year == "Выберите год" and
            rack == "Выберите стеллаж"):
            print("Нет выбранных критериев - показываем все книги")
            self.books = self.load_data_from_db()
            self.update_table()
            return
        
        try:
            # Формируем запрос в зависимости от выбранных критериев
            query_parts = []
            params = []
            
            if genre != "Выберите жанр":
                query_parts.append("genre = %s")
                params.append(genre)
                print(f"Добавлен фильтр по жанру: {genre}")
            
            if author != "Выберите автора":
                query_parts.append("author = %s")
                params.append(author)
                print(f"Добавлен фильтр по автору: {author}")
            
            if year != "Выберите год":
                try:
                    year_int = int(year)
                    query_parts.append("year = %s")
                    params.append(year_int)
                    print(f"Добавлен фильтр по году: {year}")
                except ValueError:
                    print(f"Ошибка: некорректный год '{year}'")
                    messagebox.showwarning("Ошибка", "Укажите корректный год издания!")
                    return
            
            if rack != "Выберите стеллаж":
                query_parts.append("rack = %s")
                params.append(rack)
                print(f"Добавлен фильтр по стеллажу: {rack}")
            
            # Собираем полный запрос
            if query_parts:
                where_clause = " AND ".join(query_parts)
                query = f"SELECT * FROM books WHERE {where_clause} ORDER BY rack, shelf, title"
                print(f"SQL запрос: {query}")
                print(f"Параметры: {params}")
            else:
                query = "SELECT * FROM books ORDER BY rack, shelf, title"
                print(f"SQL запрос: {query} (без параметров)")
            
            # Выполняем запрос
            self.cursor.execute(query, tuple(params))
            books = self.cursor.fetchall()
            print(f"Найдено записей в БД: {len(books)}")
            
            # Конвертируем и обновляем таблицу
            result = []
            for i, book in enumerate(books, start=1):
                book_dict = {}
                for key, value in book.items():
                    if key == 'id':
                        book_dict[key] = i
                    elif hasattr(value, 'isoformat'):
                        book_dict[key] = value.isoformat()
                    else:
                        book_dict[key] = str(value) if value is not None else ""
                result.append(book_dict)
            
            self.update_table(result)
            print(f"Обновлено строк в таблице: {len(result)}")
            
            # Формируем текст для статусной строки
            filter_texts = []
            if genre != "Выберите жанр":
                filter_texts.append(f"жанр: {genre}")
            if author != "Выберите автора":
                filter_texts.append(f"автор: {author}")
            if year != "Выберите год":
                filter_texts.append(f"год: {year}")
            if rack != "Выберите стеллаж":
                filter_texts.append(f"стеллаж: {rack}")
            
            if filter_texts:
                filter_info = " и ".join(filter_texts)
                status_text = f"Найдено книг по фильтру ({filter_info}): {len(result)}"
            else:
                status_text = f"Отображены все книги: {len(result)}"
            
            self.status_bar.config(text=status_text)
            print(f"Статус: {status_text}")
            
            # Показываем сообщение если ничего не найдено
            if len(result) == 0 and (genre != "Выберите жанр" or author != "Выберите автора" or year != "Выберите год" or rack != "Выберите стеллаж"):
                messagebox.showinfo("Результат поиска", 
                                  f"Книги по выбранным критериям не найдены.\n\n"
                                  f"Критерии поиска:\n"
                                  f"{'• Жанр: ' + genre if genre != 'Выберите жанр' else ''}\n"
                                  f"{'• Автор: ' + author if author != 'Выберите автора' else ''}\n"
                                  f"{'• Год: ' + year if year != 'Выберите год' else ''}\n"
                                  f"{'• Стеллаж: ' + rack if rack != 'Выберите стеллаж' else ''}")
                print("НИЧЕГО НЕ НАЙДЕНО!")
            
            print("="*50 + "\n")
            
        except ValueError as ve:
            print(f"Ошибка значения: {ve}")
            messagebox.showwarning("Ошибка", "Укажите корректный год издания!")
        except Error as e:
            print(f"Ошибка при комбинированной фильтрации: {e}")
            messagebox.showerror("Ошибка", f"Не удалось применить фильтр: {str(e)}")

    def filter_by_author(self, selected_author):
        """Фильтрация по выбранному автору"""
        if selected_author == "Выберите автора":
            return
        
        try:
            query = "SELECT * FROM books WHERE author = %s ORDER BY title"
            self.cursor.execute(query, (selected_author,))
            books = self.cursor.fetchall()
            
            result = []
            for i, book in enumerate(books, start=1):
                book_dict = {}
                for key, value in book.items():
                    if key == 'id':
                        book_dict[key] = i
                    elif hasattr(value, 'isoformat'):
                        book_dict[key] = value.isoformat()
                    else:
                        book_dict[key] = str(value) if value is not None else ""
                result.append(book_dict)
            
            self.update_table(result)
            self.status_bar.config(text=f"Найдено книг автора '{selected_author}': {len(result)}")
            
        except Error as e:
            print(f"Ошибка при фильтрации по автору: {e}")
            messagebox.showerror("Ошибка", f"Не удалось применить фильтр: {str(e)}")

    def filter_by_year(self, selected_year):
        """Фильтрация по выбранному году"""
        if selected_year == "Выберите год":
            return
        
        try:
            year = int(selected_year)
            query = "SELECT * FROM books WHERE year = %s ORDER BY title"
            self.cursor.execute(query, (year,))
            books = self.cursor.fetchall()
            
            result = []
            for i, book in enumerate(books, start=1):
                book_dict = {}
                for key, value in book.items():
                    if key == 'id':
                        book_dict[key] = i
                    elif hasattr(value, 'isoformat'):
                        book_dict[key] = value.isoformat()
                    else:
                        book_dict[key] = str(value) if value is not None else ""
                result.append(book_dict)
            
            self.update_table(result)
            self.status_bar.config(text=f"Найдено книг за {selected_year} год: {len(result)}")
            
        except ValueError:
            messagebox.showwarning("Ошибка", "Выберите корректный год!")
        except Error as e:
            print(f"Ошибка при фильтрации по году: {e}")
            messagebox.showerror("Ошибка", f"Не удалось применить фильтр: {str(e)}")

    def clear_filters(self):
        """Очистка всех фильтров"""
        self.genre_var.set("Выберите жанр")
        self.author_var.set("Выберите автора")
        self.year_var.set("Выберите год")
        self.isbn_entry.delete(0, tk.END)
        
        # Перезагружаем данные
        self.books = self.load_data_from_db()
        self.update_table()
        self.status_bar.config(text="Все фильтры очищены. Отображены все книги.")

    def show_all_books(self):
        """Показать все книги"""
        self.books = self.load_data_from_db()
        self.update_table()
        self.clear_filters()
        self.status_bar.config(text=f"Отображены все книги. Всего: {len(self.books)}")

    def reset_search_filters(self):
        """Сброс всех фильтров и поиска"""
        self.search_entry.delete(0, tk.END)
        self.filter_entry.delete(0, tk.END)
        self.books = self.load_data_from_db()
        self.update_table()
        self.status_bar.config(text="Все фильтры сброшены. Отображены все книги.")

    def refresh_catalog(self):
        """Обновление каталога книг из базы данных"""
        try:
            # Перезагружаем данные из базы
            self.books = self.load_data_from_db()
            self.update_table()
            self.clear_form()
            self.status_bar.config(text=f"Каталог обновлен. Всего книг: {len(self.books)}")
            messagebox.showinfo("Обновление", "Каталог книг успешно обновлен из базы данных!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить каталог: {str(e)}")

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
                                added_count += 1
                    
                    # Перезагружаем все данные с обновленными ID
                    self.books = self.load_data_from_db()
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

    def on_mousewheel(self, event):
        """Прокрутка таблицы колесиком мыши"""
        try:
            # Попытка 1: Для Windows и большинства Linux
            if event.delta:
                self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return
        except AttributeError:
            pass
        
        try:
            # Попытка 2: Для macOS и некоторых Linux
            if event.num == 4:
                self.tree.yview_scroll(-1, "units")
            elif event.num == 5:
                self.tree.yview_scroll(1, "units")
        except AttributeError:
            pass
        
        # Попытка 3: Альтернативный метод
        try:
            if event.state == 0x0100:  # Shift+колесико = горизонтальная прокрутка
                self.tree.xview_scroll(-1 if event.delta > 0 else 1, "units")
            else:
                self.tree.yview_scroll(-1 if event.delta > 0 else 1, "units")
        except:
            # Если ничего не работает, просто игнорируем
            pass

    def update_filter_lists(self):
        """Обновление списков в фильтрах"""
        # Обновляем жанры
        genres = ["Выберите жанр"] + sorted(self.get_unique_genres())
        self.genre_menu['values'] = genres
        
        # Обновляем авторов
        authors = ["Выберите автора"] + sorted(self.get_unique_authors())
        self.author_menu['values'] = authors
        
        # Обновляем годы
        years = ["Выберите год"] + sorted(self.get_unique_years(), reverse=True)
        self.year_menu['values'] = years

    def get_unique_racks(self):
        """Получение уникальных стеллажей из БД"""
        try:
            query = "SELECT DISTINCT rack FROM books WHERE rack IS NOT NULL AND rack != '' ORDER BY rack"
            self.cursor.execute(query)
            racks = []
            for row in self.cursor.fetchall():
                rack = row['rack']
                if rack and rack.strip():
                    clean_rack = rack.strip().upper()
                    if clean_rack not in racks:
                        racks.append(clean_rack)
            print(f"Получено уникальных стеллажей: {len(racks)}")
            return racks
        except Error as e:
            print(f"Ошибка при получении стеллажей: {e}")
            return []


def main():
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()