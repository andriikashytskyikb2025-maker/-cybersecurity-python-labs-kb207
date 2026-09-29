import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


def main() -> None:
    print(f"Лабораторна робота №1  Виконав: {STUDENT_NAME}, група {GROUP_NAME}")
    print(f"Варіант №{VARIANT_NUMBER}\n")

    try:
        from labs.lab01 import task1
        print("\nЗавдання 1")
        task1.main()
    except Exception as e:
        print(f"[Помилка в Завданні 1]: {e}")

    try:
        from labs.lab01 import task2
        print("\nЗавдання 2")
        task2.main()
    except Exception as e:
        print(f"[Помилка в Завданні 2]: {e}")

    try:
        from labs.lab01 import task3
        print("\nЗавдання 3")
        task3.main()
    except Exception as e:
        print(f"[Помилка в Завданні 3]: {e}")


if __name__ == "__main__":
    main()