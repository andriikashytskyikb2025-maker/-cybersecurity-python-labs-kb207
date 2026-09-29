import csv
from datetime import datetime
import functools
import hashlib
import json
import os
import sys
from pathlib import Path

#Додавання кореневого шляху для імпорту
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


#Власний виняток
class ValidationError(Exception):
    pass


#Налаштування
SALT = str(VARIANT_NUMBER).zfill(5)
MIN_PASSWORD_LEN = 12
DATA_DIR = Path("labs/lab01/data")


#Хешування
def generate_hash(password: str, salt: str = "00000") -> str:
    if not password or not salt:
        raise ValueError("Пароль та сіль не можуть бути порожніми.")
    if len(password) < MIN_PASSWORD_LEN:
        raise ValidationError(
            f"Пароль занадто короткий. Мін. довжина: {MIN_PASSWORD_LEN}"
        )

    return hashlib.sha3_512(f"{password}{salt}".encode()).hexdigest()


#Реєстрація
def create_user(username: str, password: str) -> tuple[str, str]:
    if not username:
        raise ValueError("Ім'я користувача не може бути порожнім.")
    return username, generate_hash(password, SALT)


USERS_TO_REGISTER = (
    ("m_kovalenko", "Kov@lenko_Sec2026!"),
    ("s_tech_lead", "Arch_SySt3m#9901"),
    ("dev_back_end", "PyTh0n_D3v_K3y!9"),
    ("sys_admin_main", "R00t_Acc3ss_P@ss!"),
    ("qa_automation", "T3st_AUt0m@ti0n#1"),
    ("cloud_engineer", "AWS_Cl0ud_S3cur3!"),
    ("db_architect", "PostgreS_DB#Key26"),
    ("infosec_officer", "CISO_Gu@rd_Pass!1"),
    ("soc_analyst_l1", "M0nit0r_S0C_L1#99"),
    ("devops_pipeline", "GitL@b_CI_CD_2026"),
)

def create_users(users_list: tuple) -> None:
    file_path = DATA_DIR / "users.csv"
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for user, pwd in users_list:
                writer.writerow(create_user(user, pwd))
    except PermissionError:
        print(f"[ERROR] Відсутні права на запис у директорію: {DATA_DIR}")
        raise
    except (IOError, OSError) as e:
        print(f"[ERROR] Помилка введення-виведення під час створення бази: {e}")
        raise


#Читання бази даних
def read_users_db() -> list[tuple[str, str]]:
    file_path = DATA_DIR / "users.csv"
    try:
        with file_path.open("r", encoding="utf-8") as file:
            users_db = [tuple(row) for row in csv.reader(file) if row]

        print("\n" + "=" * 70)
        print(f"{'Користувач':<20} | {'Хеш пароля':<45}")
        print("=" * 70)
        for user, h_val in users_db:
            print(f"{user:<20} | {h_val:<45}")
        print("=" * 70)

        return users_db
    except FileNotFoundError:
        print(f"[ERROR] Файл бази даних не знайдено за шляхом: {file_path}")
        return []
    except PermissionError:
        print(f"[ERROR] Немає прав на читання файлу: {file_path}")
        return []
    except (IOError, OSError) as e:
        print(f"[ERROR] Збій читання бази даних: {e}")
        return []


#Логування
def log_event(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        username = args[0] if args else kwargs.get("username", "unknown")

        # Маскуємо пароль у логах задля безпеки
        safe_args = [args[0], "***HIDDEN***"] if len(args) >= 2 else list(args)
        safe_kwargs = {k: ("***HIDDEN***" if k == "password" else v) for k, v in kwargs.items()}

        try:
            success = func(*args, **kwargs)
            status = "success" if success else "failure"
        except (ValueError, ValidationError):
            status = "failure"
            raise
        except Exception:
            status = "failure"
            raise
        finally:
            log_file = DATA_DIR / "log.json"
            try:
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                logs = []
                if log_file.exists():
                    try:
                        logs = json.loads(log_file.read_text(encoding="utf-8"))
                    except (json.JSONDecodeError, IOError):
                        logs = []

                logs.append({
                    "event": "login",
                    "user": username,
                    "result": status,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "args": safe_args,
                    "kwargs": safe_kwargs
                })
                log_file.write_text(
                    json.dumps(logs, ensure_ascii=False, indent=4), encoding="utf-8"
                )
            except (PermissionError, IOError) as e:
                print(f"[LOG WARNING] Не вдалося записати аудит-лог: {e}")

        return success

    return wrapper


#Автентифікація
@log_event
def login(username: str, password: str, users_db: list) -> bool:
    if not username or not password:
        raise ValueError("Логін та пароль не можуть бути порожніми.")

    expected_hash = dict(users_db).get(username)
    if expected_hash:
        return generate_hash(password, SALT) == expected_hash
    return False


def safe_login_demo(username: str, password: str, users_db: list) -> bool:
    try:
        res = login(username, password, users_db)
        msg = (
            f"Користувач '{username}' успішно увійшов."
            if res
            else f"Неправильні дані для '{username}'."
        )
        print(f"[УСПІХ] {msg}" if res else f"[ВІДМОВА] {msg}")
        return res
    except ValidationError as e:
        print(f"[VALIDATION_ERROR] {e}")
        return False
    except ValueError as e:
        print(f"[VALUE_ERROR] {e}")
        return False
    except PermissionError:
        print("[SECURITY_ERROR] Помилка доступу до файлової системи при аутентифікації.")
        return False
    except (IOError, OSError):
        print("[SYSTEM_ERROR] Системна помилка обробки файлів.")
        return False



#Головна функція
def main():
    print("Виконання Завдання 3")
    print(f"Студент: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}\n")

    try:
        print("--> Створення та читання CSV-бази даних...")
        create_users(USERS_TO_REGISTER)
        db = read_users_db()

        if db:
            print("\n--> Тестування входу...")
            safe_login_demo("m_kovalenko", "Kov@lenko_Sec2026!", db)
            safe_login_demo("m_kovalenko", "wrong_pass_12345", db)
            safe_login_demo("m_kovalenko", "short", db)
            safe_login_demo("", "Kov@lenko_Sec2026!", db)

    except (FileNotFoundError, PermissionError, IOError) as e:
        print(f"[КРИТИЧНА ПОМИЛКА ФАЙЛОВОЇ СИСТЕМИ] {e}")
    except (ValueError, ValidationError) as e:
        print(f"[ПОМИЛКА ВАЛІДАЦІЇ] {e}")


if __name__ == "__main__":
    main()