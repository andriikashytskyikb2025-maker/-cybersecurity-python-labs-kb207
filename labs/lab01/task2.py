import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

# Базові дані модуля
users = {
    "admin001": {"role": "administrator", "clearance": 4, "department": "IT", "active": True},
    "user123": {"role": "analyst", "clearance": 2, "department": "Security", "active": True},
    "guest789": {"role": "guest", "clearance": 1, "department": "External", "active": True},
    "manager456": {"role": "manager", "clearance": 3, "department": "Operations", "active": True},
    "contractor99": {"role": "contractor", "clearance": 1, "department": "External", "active": False}
}

resources = [
    ("database_backup", 4), ("user_logs", 2), ("public_docs", 1),
    ("financial_reports", 3), ("system_config", 4), ("training_materials", 1),
    ("security_policies", 3), ("audit_logs", 4), ("employee_data", 3),
    ("temp_files", 1)
]

security_levels = ("Public", "Internal", "Confidential", "Secret")
blocked_users = {"contractor99", "temp_user", "suspended_acc"}


def check_access(user_key: str, req_clearance: int) -> tuple[bool, str]:
    if user_key not in users:
        return False, "Користувача не знайдено"

    user_info = users[user_key]

    if user_key in blocked_users:
        return False, "Заблоковано"
    if not user_info["active"]:
        return False, "Неактивний акаунт"

    if user_info["clearance"] >= req_clearance:
        return True, "Дозволено"

    return False, "Недостатньо прав"


def main():
    print("Виконання Завдання 2")
    print(f"Студент: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}\n")

    print("--- Список ресурсів та рівнів допуску ---")
    for res_name, req_level in resources:
        level_name = security_levels[req_level - 1]
        print(f"{res_name:<20} / {level_name}")

    print("\n--- Результати перевірки доступу ---")
    print(f"{'Користувач':<15} / {'Ресурс':<20} / {'Статус':<8} / {'Причина відмови'}")
    print("-" * 65)

    for user_key in users:
        for res_name, req_level in resources:
            allowed, status_msg = check_access(user_key, req_level)
            access_str = "Allow" if allowed else "Deny"
            print(f"{user_key:<15} / {res_name:<20} / {access_str:<8} / {status_msg}")


if __name__ == "__main__":
    main()