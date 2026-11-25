def ask(message):
    return input(message).strip()


def run_menu(system, user):
    while True:
        print("\n=== INVENTORY MENU ===")
        print("1. Show Products")
        if user.can("add_product"):
            print("2. Add Product")
        print("3. Search Product")
        print("0. Exit")

        choice = ask("Choose option: ")

        if choice == "1":
            system.show_products(user)
        elif choice == "2" and user.can("add_product"):
            system.add_product(user)
        elif choice == "3":
            system.search_product(user)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")