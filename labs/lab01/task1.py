import os
import random
import sys

# Додавання кореневого шляху для імпорту
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

# Базові дані модуля
passwords = [
    "password123",
    "Qwerty!2023",
    "admin",
    "MyP@ssw0rd",
    "123456",
    "SecurePass!",
    "test",
    "P@ssw0rd123",
    "welcome",
    "StrongP@ss1",
]

criteria = {
    "min_length": 8,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

forbidden_passwords = {"password", "123456", "admin", "test", "welcome", "qwerty"}


def evaluate_password(password, passwords_list, crit, forbidden):
    if password in forbidden or len(password) < crit["min_length"]:
        return "Заборонений / Дуже слабкий"

    has_digit = any(c.isdigit() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_special = any(not c.isalnum() for c in password)

    all_criteria_met = has_digit and has_upper and has_special
    is_unique = passwords_list.count(password) == 1

    if all_criteria_met and len(password) >= crit["min_length"] + 4 and is_unique:
        return "Дуже сильний"
    elif all_criteria_met:
        return "Сильний"
    elif has_digit or has_upper or has_special:
        return "Середній"
    else:
        return "Дуже слабкий"


def main():
    print("Виконання Завдання 1")
    print(f"Студент: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}\n")

    # Симуляція появи дублікатів паролів
    working_passwords = passwords.copy()
    for _ in range(3):
        used_pass = random.choice(working_passwords)
        working_passwords.append(used_pass)

    print(f"{'Пароль':<20} | {'Стійкість'}")
    print("-" * 45)

    for pswd in working_passwords:
        status = evaluate_password(pswd, working_passwords, criteria, forbidden_passwords)
        print(f"{pswd:<20} | {status}")


if __name__ == "__main__":
    main()