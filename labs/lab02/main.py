import sys
import time
from labs.lab02.task1 import User, Admin, UserAccount, SESSION_TIMEOUT_SEC

def run_demo():
    print("=== ДЕМОНСТРАЦІЯ ЛАБОРАТОРНОЇ РОБОТИ №2 ===")

    # 1. Створення користувача та встановлення пароля
    print("\n--- 1. Створення користувача ---")
    user = User(username="usr_john", email="john.doe@example.com")
    user.set_password("SecretPassword123")
    account = UserAccount(user=user)
    print(f"Створено об'єкт: {user}")

    # 2. Валідація Email
    print("\n--- 2. Валідація Email ---")
    try:
        account["email"] = "invalid-email"
    except ValueError as e:
        print(f"Спіймано очікувану помилку email: {e}")

    account["email"] = "john_new@domain.org"
    print(f"Оновлений email: {account['email']}")

    # 3. Невдалий та успішний вхід
    print("\n--- 3. Спроби входу (Login) ---")
    login_fail = account.login("usr_john", "WrongPassword", ip="192.168.1.10")
    print(f"Спроба з неправильним паролем: {'Успіх' if login_fail else 'Невдача'}")

    login_success = account.login("usr_john", "SecretPassword123", ip="192.168.1.10")
    print(f"Спроба з правильним паролем: {'Успіх' if login_success else 'Невдача'}")
    print(f"Чи автентифікований сеанс? {account.is_authenticated()}")

    # 4. Демонстрація Admin
    print("\n--- 4. Робота з Admin ---")
    admin = Admin(username="admin_alex", email="alex.admin@company.com")
    admin.grant_permission("READ")
    admin.grant_permission("WRITE")
    admin.grant_permission("DELETE")
    print(admin)
    print(f"Чи має право 'DELETE'? {admin.has_permission('DELETE')}")
    admin.revoke_permission("DELETE")
    print(f"Після відкликання, чи має право 'DELETE'? {admin.has_permission('DELETE')}")

    # 5. Перевірка таймауту сеансу
    print("\n--- 5. Перевірка таймауту сеансу ---")
    print("Штучна перевірка з маленьким таймаутом (1 секунда)...")
    time.sleep(1.5)
    print(f"Чи активний сеанс із timeout=1s? {account.session.is_active(timeout_sec=1)}")
    print(f"Чи активний сеанс зі стандартним SESSION_TIMEOUT_SEC ({SESSION_TIMEOUT_SEC}s)? {account.is_authenticated()}")

    # 6. Вихід із системи (Logout)
    print("\n--- 6. Вихід із системи ---")
    account.logout()
    print(f"Чи автентифікований після logout? {account.is_authenticated()}")

    # 7. Перегляд журналу AuditLog
    print("\n--- 7. Журнал AuditLog ---")
    for log in account.audit_log.show_all():
        print(log)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo()
    else:
        print("Для запуску демонстрації виконайте команду:")
        print("python -m labs.lab02.main demo")