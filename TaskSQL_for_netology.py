"""
Требуется хранить персональную информацию о клиентах:
-имя,
-фамилия,
-email,
-телефон.

Сложность в том, что телефон у клиента может быть не один, а два, три и даже больше. А может и вообще не быть телефона,
например, он не захотел его оставлять.

Вам необходимо разработать структуру БД для хранения информации и несколько функций на Python для управления данными.

Функция, создающая структуру БД (таблицы).
Функция, позволяющая добавить нового клиента.
Функция, позволяющая добавить телефон для существующего клиента.
Функция, позволяющая изменить данные о клиенте.
Функция, позволяющая удалить телефон для существующего клиента.
Функция, позволяющая удалить существующего клиента.
Функция, позволяющая найти клиента по его данным: имени, фамилии, email или телефону.
Функции выше являются обязательными, но это не значит, что должны быть только они.
При необходимости можете создавать дополнительные функции и классы.
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
PASSWORD_DB = os.getenv("PASSWORD_DB")
NAME_DB = os.getenv("NAME_DB")

class Database:
    """Класс инкапсулирует логику работы с базой данных."""
    def __init__(self, dbname, user, password):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.connection = None

    def connect(self):
        """Устанавливает соединение с базой данных."""
        self.connection = psycopg2.connect(database=self.dbname, user=self.user, password=self.password)

    def close(self):
        """Закрывает соединение, если оно открыто."""
        if self.connection:
            self.connection.close()

    def execute(self, query, params=None):
        """Выполняет запрос query с параметрами params."""
        with self.connection.cursor() as cur:
            cur.execute(query, params)
            self.connection.commit()

    def fetchone(self, query, params=None):
        """Выполняет запрос и возвращает одну строку результата."""
        with self.connection.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def fetchall(self, query, params=None):
        """Выполняет запрос и возвращает все строки результата."""
        with self.connection.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


class Client:
    """Класс для работы с клиентами."""
    def __init__(self, db, first_name, last_name, email):
        self.db = db
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.id = None
        self.phones = []

    def save(self):
        """Сохраняет клиента в таблице clients."""
        query = """
            INSERT INTO clients (first_name, last_name, email)
            VALUES (%s, %s, %s) RETURNING id;
        """
        self.db.execute(query, (self.first_name, self.last_name, self.email))
        self.id = self.db.fetchone(query, (self.first_name, self.last_name, self.email))[0]

    def add_phone(self, phone_number):
        """Создаёт объект телефона (Phone), сохраняет его в базе и добавляет в список phones."""
        phone = Phone(self.db, self, phone_number)
        phone.save()
        self.phones.append(phone)

    def update(self, first_name=None, last_name=None, email=None):
        """Обновляет данные клиента в базе."""
        if first_name: self.first_name = first_name
        if last_name: self.last_name = last_name
        if email: self.email = email

        query = """
            UPDATE clients SET first_name = %s, last_name = %s, email = %s WHERE id = %s;
        """
        self.db.execute(query, (self.first_name, self.last_name, self.email, self.id))

    def delete(self):
        """Удаляет клиента и все его телефоны из базы."""
        query = """
            DELETE FROM clients WHERE id = %s;
        """
        self.db.execute(query, (self.id,))
        for phone in self.phones:
            phone.delete()

    def find_by_id(self):
        """Возвращает данные клиента по его id."""
        query = """
            SELECT * FROM clients WHERE id = %s;
        """
        return self.db.fetchone(query, (self.id,))

    def __repr__(self):
        """Строковое представление объекта."""
        return f"Client({self.first_name}, {self.last_name}, {self.email})"


class Phone:
    """Класс для работы с телефонами."""
    def __init__(self, db, client, phone_number):
        self.db = db
        self.client = client
        self.phone_number = phone_number

    def save(self):
        """Сохраняет номер телефона в таблице phones."""
        query = """
            INSERT INTO phones (client_id, phone)
            VALUES (%s, %s);
        """
        self.db.execute(query, (self.client.id, self.phone_number))

    def delete(self):
        """Удаляет телефон из базы."""
        query = """
            DELETE FROM phones WHERE client_id = %s AND phone = %s;
        """
        self.db.execute(query, (self.client.id, self.phone_number))

    def __repr__(self):
        """Строковое представление телефона."""
        return f"Phone({self.phone_number})"


if __name__ == "__main__":
    # Подключаемся к базе данных
    db = Database(dbname=NAME_DB, user="postgres", password=PASSWORD_DB)
    db.connect()

    # Создаём таблицы
    db.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            email VARCHAR(100) UNIQUE
        );
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS phones (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            phone VARCHAR(20) NOT NULL
        );
    """)

    # Создаём клиента
    client1 = Client(db, "Иван", "Иванов", "ivanovv@example.com")
    client1.save()  # Сохраняем клиента в базе

    # Добавляем телефоны для клиента
    client1.add_phone("+79161234567")
    client1.add_phone("+79161234568")

    # Изменяем данные клиента
    client1.update(first_name="Иван", last_name="Сидоров", email="sidorov@example.com")

    # Поиск клиента по ID
    print(client1.find_by_id())

    # Удаляем клиента и его телефоны
    client1.delete()

    db.close()