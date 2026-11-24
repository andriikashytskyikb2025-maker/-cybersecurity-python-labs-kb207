import sqlite3
from contextlib import closing
from typing import Optional, List, Dict, Any, Tuple
from labs.lab03.database import get_connection


def create_category(name: str) -> Optional[Dict[str, Any]]:
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE name = ?", (name,))
        if cursor.fetchone():
            return None
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        return {"id": cursor.lastrowid, "name": name}


def get_categories() -> List[Dict[str, Any]]:
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories ORDER BY id ASC")
        return [dict(row) for row in cursor.fetchall()]


def delete_category(category_id: int) -> str:
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE id = ?", (category_id,))
        if not cursor.fetchone():
            return "NOT_FOUND"

        cursor.execute("SELECT COUNT(*) FROM records WHERE category_id = ?", (category_id,))
        if cursor.fetchone()[0] > 0:
            return "HAS_RECORDS"

        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        return "SUCCESS"


def get_record_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.id, r.code, r.title, r.category_id, c.name AS category_name, r.value, r.status
            FROM records r
            JOIN categories c ON r.category_id = c.id
            WHERE r.id = ?
            """,
            (record_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_record(code: str, title: str, category_id: int, value: float, status: str) -> Tuple[
    str, Optional[Dict[str, Any]]]:
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE id = ?", (category_id,))
        if not cursor.fetchone():
            return "CATEGORY_NOT_FOUND", None

        cursor.execute("SELECT id FROM records WHERE code = ?", (code,))
        if cursor.fetchone():
            return "DUPLICATE_CODE", None

        cursor.execute(
            "INSERT INTO records (code, title, category_id, value, status) VALUES (?, ?, ?, ?, ?)",
            (code, title, category_id, value, status)
        )
        conn.commit()
        return "SUCCESS", get_record_by_id(cursor.lastrowid)


def get_records(category_id: Optional[int] = None, status: Optional[str] = None,
                min_value: Optional[float] = None, q: Optional[str] = None,
                limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT r.id, r.code, r.title, r.category_id, c.name AS category_name, r.value, r.status
            FROM records r
            JOIN categories c ON r.category_id = c.id
            WHERE 1=1
        """
        params: List[Any] = []

        if category_id is not None:
            query += " AND r.category_id = ?"
            params.append(category_id)
        if status is not None:
            query += " AND r.status = ?"
            params.append(status)
        if min_value is not None:
            query += " AND r.value >= ?"
            params.append(min_value)
        if q is not None:
            query += " AND instr(r.title, ?) > 0"
            params.append(q)

        query += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def update_record(record_id: int, code: str, title: str, category_id: int, value: float, status: str) -> Tuple[
    str, Optional[Dict[str, Any]]]:
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM records WHERE id = ?", (record_id,))
        if not cursor.fetchone():
            return "RECORD_NOT_FOUND", None

        cursor.execute("SELECT id FROM categories WHERE id = ?", (category_id,))
        if not cursor.fetchone():
            return "CATEGORY_NOT_FOUND", None

        cursor.execute("SELECT id FROM records WHERE code = ? AND id != ?", (code, record_id))
        if cursor.fetchone():
            return "DUPLICATE_CODE", None

        cursor.execute(
            "UPDATE records SET code = ?, title = ?, category_id = ?, value = ?, status = ? WHERE id = ?",
            (code, title, category_id, value, status, record_id)
        )
        conn.commit()
        return "SUCCESS", get_record_by_id(record_id)


def delete_record(record_id: int) -> bool:
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM records WHERE id = ?", (record_id,))
        if not cursor.fetchone():
            return False
        cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()
        return True


def create_records_batch(records_list: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    with closing(get_connection()) as conn:
        cursor = conn.cursor()

        codes_in_batch = [r["code"] for r in records_list]
        if len(codes_in_batch) != len(set(codes_in_batch)):
            return "DUPLICATE_CODE_IN_BATCH", []

        category_ids = {r["category_id"] for r in records_list}
        for cat_id in category_ids:
            cursor.execute("SELECT id FROM categories WHERE id = ?", (cat_id,))
            if not cursor.fetchone():
                return "CATEGORY_NOT_FOUND", []

        for code in codes_in_batch:
            cursor.execute("SELECT id FROM records WHERE code = ?", (code,))
            if cursor.fetchone():
                return "DUPLICATE_CODE_DB", []

        created_ids = []
        try:
            for r in records_list:
                cursor.execute(
                    "INSERT INTO records (code, title, category_id, value, status) VALUES (?, ?, ?, ?, ?)",
                    (r["code"], r["title"], r["category_id"], r["value"], r["status"])
                )
                created_ids.append(cursor.lastrowid)
            conn.commit()
        except sqlite3.Error:
            conn.rollback()
            return "TRANSACTION_ERROR", []

        return "SUCCESS", [get_record_by_id(rid) for rid in created_ids]