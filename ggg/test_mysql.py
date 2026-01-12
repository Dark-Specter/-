import mysql.connector
from mysql.connector import Error

try:
    # Подключение к базе данных
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='vada/228',
        database='library_db'
    )
    
    if connection.is_connected():
        print("✅ Успешное подключение к MySQL!")
        
        # Получение информации о сервере
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"Версия MySQL: {version[0]}")
        
        # Проверка существования таблицы books
        cursor.execute("SHOW TABLES LIKE 'books'")
        result = cursor.fetchone()
        if result:
            print("✅ Таблица 'books' существует")
            
            # Подсчет книг
            cursor.execute("SELECT COUNT(*) FROM books")
            count = cursor.fetchone()[0]
            print(f"Количество книг в базе: {count}")
        else:
            print("❌ Таблица 'books' не найдена")
            
except Error as e:
    print(f"❌ Ошибка подключения: {e}")
    
finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("Соединение закрыто")