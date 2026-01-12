-- ============================================
-- БИБЛИОТЕКА: СОЗДАНИЕ БАЗЫ ДАННЫХ И ТАБЛИЦ
-- ============================================

-- 1. СОЗДАНИЕ БАЗЫ ДАННЫХ
DROP DATABASE IF EXISTS library_db;
CREATE DATABASE library_db;

-- 2. ВЫБОР БАЗЫ ДАННЫХ ДЛЯ РАБОТЫ
USE library_db;

-- 3. СОЗДАНИЕ ТАБЛИЦЫ КНИГ
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Проверки для целостности данных
    CHECK (year > 0 AND year <= YEAR(CURRENT_DATE)),
    CHECK (quantity >= 0)
);

-- 4. СОЗДАНИЕ ИНДЕКСОВ ДЛЯ БЫСТРОГО ПОИСКА
CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_books_author ON books(author);
CREATE INDEX idx_books_genre ON books(genre);
CREATE INDEX idx_books_isbn ON books(isbn);
CREATE INDEX idx_books_year ON books(year);

-- 5. ВСТАВКА ТЕСТОВЫХ ДАННЫХ
INSERT INTO books (title, author, year, genre, publisher, isbn, quantity, location) VALUES
('Мастер и Маргарита', 'Михаил Булгаков', 1967, 'Роман', 'Художественная литература', '978-5-389-12345-6', 5, 'Стеллаж A, Полка 3'),
('Преступление и наказание', 'Фёдор Достоевский', 1866, 'Роман', 'Эксмо', '978-5-699-54321-0', 3, 'Стеллаж B, Полка 1'),
('Война и мир', 'Лев Толстой', 1869, 'Роман', 'АСТ', '978-5-17-098765-4', 4, 'Стеллаж C, Полка 2'),
('1984', 'Джордж Оруэлл', 1949, 'Антиутопия', 'Penguin Books', '978-0-14-103614-4', 2, 'Стеллаж A, Полка 4'),
('Гарри Поттер и философский камень', 'Джоан Роулинг', 1997, 'Фэнтези', 'Росмэн', '978-5-353-01234-5', 6, 'Стеллаж D, Полка 1'),
('Маленький принц', 'Антуан де Сент-Экзюпери', 1943, 'Философская сказка', 'Эксмо', '978-5-699-67890-1', 4, 'Стеллаж B, Полка 2'),
('Три товарища', 'Эрих Мария Ремарк', 1936, 'Роман', 'АСТ', '978-5-17-112233-4', 3, 'Стеллаж C, Полка 3');

-- 6. ПРОСМОТР СОЗДАННОЙ ТАБЛИЦЫ
SELECT '=== СОЗДАННЫЕ ТАБЛИЦЫ ===' AS '';
SHOW TABLES;

SELECT '=== СОДЕРЖИМОЕ ТАБЛИЦЫ books ===' AS '';
SELECT * FROM books;

-- 7. ПРОСМОТР СТРУКТУРЫ ТАБЛИЦЫ
SELECT '=== СТРУКТУРА ТАБЛИЦЫ books ===' AS '';
DESCRIBE books;