"""Start of the program (run this file)

Default login:  username = admin   password = admin123
"""

from system import InventorySystem
from ui import ask, run_menu


def main():
    system = InventorySystem()
    print("=== INVENTORY AND WAREHOUSE SYSTEM ===")
    user = None
    for _ in range(3):
        user = system.login(ask("Username: "), ask("Password: "))
        if user:
            break
        print("Wrong username or password.")
    if user is None:
        print("Too many failed attempts.")
        return

    # Show low-stock warning right after login
    if user.can("low_stock"):
        low = system.low_stock_products(user)
        if low:
            print(f"\nWARNING: {len(low)} product(s) are below minimum stock!")
    run_menu(system, user)


if __name__ == "__main__":
    main()
