import json
import sqlite3
from contextlib import closing
from labs.lab03.database import get_connection, BASE_DIR, initialize_database

# Шлях до папки data у корені проєкту
SEED_PATH = BASE_DIR.parent.parent / "data" / "seed.json"


def seed_database() -> None:
    if not SEED_PATH.exists():
        print(f"Помилка: Файл {SEED_PATH} не знайдено.")
        return

    with open(SEED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    categories = data.get("categories", [])
    records = data.get("records", [])

    # Гарантуємо, що таблиці існують перед заповненням
    initialize_database()

    with closing(get_connection()) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] > 0:
            print("База даних вже містить дані. Заповнення скасовано без змін.")
            return

        try:
            cursor.executemany(
                "INSERT INTO categories (id, name) VALUES (:id, :name)",
                categories
            )
            cursor.executemany(
                """
                INSERT INTO records (code, title, category_id, value, status)
                VALUES (:code, :title, :category_id, :value, :status)
                """,
                records
            )
            conn.commit()
            print("Початкове заповнення для Варіанта 1 успішно виконано!")
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Помилка в початкових даних, транзакцію скасовано: {e}")


if __name__ == "__main__":
    seed_database()