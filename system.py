"""Business logic, rules, permission checks, JSON file saving."""

import hashlib
import json
from datetime import datetime

from models import Category, Supplier, Product, StockTransaction
from users import User
from ui import ask

DATA_FILE = "inventory_data.json"


def hash_password(password):
    """users.py has no hashing, so system.py does it."""
    return hashlib.sha256(password.encode()).hexdigest()


class InventorySystem:
    def __init__(self):
        self.categories = []
        self.suppliers = []
        self.products = []
        self.users = []
        self.transactions = []
        self.load()

    # ---------- File handling ----------
    def load(self):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            self.categories = [Category(**c) for c in data["categories"]]
            self.suppliers = [Supplier(**s) for s in data["suppliers"]]
            self.products = [Product(**p) for p in data["products"]]
            # User.password stores the HASH (never the plain password)
            self.users = [User(u["username"], u["password_hash"], u["role"])
                          for u in data["users"]]
            self.transactions = [StockTransaction(**t) for t in data["transactions"]]
        except FileNotFoundError:
            self.create_defaults()
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            print("Data file is damaged. Starting with default data.")
            self.create_defaults()

    def create_defaults(self):
        self.categories = [Category(1, "General")]
        self.suppliers = []
        self.products = []
        self.transactions = []
        self.users = [User("admin", hash_password("admin123"), "admin")]
        self.save()

    def save(self):
        data = {
            "categories": [c.to_dict() for c in self.categories],
            "suppliers": [s.to_dict() for s in self.suppliers],
            "products": [p.to_dict() for p in self.products],
            "users": [{"username": u.username, "password_hash": u.password,
                       "role": u.role} for u in self.users],
            "transactions": [t.to_dict() for t in self.transactions],
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

    # ---------- Helpers ----------
    def check(self, user, action):
        """Permission check - stops unauthorized users."""
        if not user.can(action):
            raise PermissionError(f"Access denied. {user.role} cannot do this.")

    def login(self, username, password):
        for u in self.users:
            if u.username == username and u.password == hash_password(password):
                return u
        return None

    def find_category(self, cat_id):
        for c in self.categories:
            if c.cat_id == cat_id:
                return c
        return None

    def find_supplier(self, supplier_id):
        for s in self.suppliers:
            if s.supplier_id == supplier_id:
                return s
        return None

    def find_product(self, product_id):
        for p in self.products:
            if p.product_id == product_id.upper():
                return p
        return None

    def get_product(self, product_id):
        p = self.find_product(product_id)
        if p is None:
            raise ValueError("Product not found.")
        return p

    def category_name(self, cat_id):
        c = self.find_category(cat_id)
        return c.name if c else "-"

    def supplier_name(self, supplier_id):
        s = self.find_supplier(supplier_id)
        return s.name if s else "-"

    def next_id(self, items, attr):
        return max([getattr(i, attr) for i in items], default=0) + 1

    # ---------- Products (logic) ----------
    def list_products(self, user):
        self.check(user, "view_products")
        can_see_all = user.can("add_product")      # admins also see deactivated products
        return [p for p in self.products if p.active or can_see_all]

    def search_products(self, user, keyword):
        self.check(user, "search_product")
        keyword = keyword.lower()
        results = []
        for p in self.list_products(user):
            text = [p.product_id, p.name, self.category_name(p.category_id), p.shelf]
            if any(keyword in t.lower() for t in text):
                results.append(p)
        return results

    def create_product(self, user, product_id, name, category_id,
                       price, quantity, shelf, min_stock):
        self.check(user, "add_product")
        product_id = product_id.upper()
        if product_id == "" or name == "":
            raise ValueError("Product ID and name are required.")
        if self.find_product(product_id):
            raise ValueError("Product ID already exists.")
        if not self.find_category(category_id):
            raise ValueError("Every product must belong to a valid category.")
        if min_stock < 0:
            raise ValueError("Minimum stock cannot be negative.")
        # Product's setters check price > 0 and quantity >= 0
        self.products.append(Product(product_id, name, category_id,
                                     price, quantity, shelf, min_stock))
        self.save()

    def update_product(self, user, product_id, name=None, category_id=None,
                       price=None, shelf=None):
        self.check(user, "manage_products")
        p = self.get_product(product_id)
        if category_id is not None and not self.find_category(category_id):
            raise ValueError("Category not found.")
        if name:
            p.name = name
        if category_id is not None:
            p.category_id = category_id
        if price is not None:
            p.price = price
        if shelf:
            p.shelf = shelf
        self.save()

    def delete_product(self, user, product_id):
        self.check(user, "manage_products")
        p = self.get_product(product_id)
        has_history = any(t.product_id == p.product_id for t in self.transactions)
        if has_history:
            p.active = False          # keep history, only deactivate
            message = "Product has transaction history, so it was DEACTIVATED."
        else:
            self.products.remove(p)
            message = "Product deleted."
        self.save()
        return message

    def set_min_stock(self, user, product_id, value):
        self.check(user, "set_min_stock")
        if value < 0:
            raise ValueError("Minimum stock cannot be negative.")
        self.get_product(product_id).min_stock = value
        self.save()

    # ---------- Stock In / Out ----------
    def record_transaction(self, product_id, kind, quantity, supplier_id, username):
        tx = StockTransaction(self.next_id(self.transactions, "tx_id"),
                              product_id, kind, quantity, supplier_id,
                              datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username)
        self.transactions.append(tx)

    def stock_in(self, user, product_id, quantity, supplier_id):
        self.check(user, "stock_in")
        p = self.get_product(product_id)
        if not p.active:
            raise ValueError("This product is deactivated.")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        if not self.find_supplier(supplier_id):
            raise ValueError("Supplier not found.")
        p.quantity += quantity
        self.record_transaction(p.product_id, "IN", quantity, supplier_id, user.username)
        self.save()
        return p

    def stock_out(self, user, product_id, quantity):
        self.check(user, "stock_out")
        p = self.get_product(product_id)
        if not p.active:
            raise ValueError("This product is deactivated.")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        if quantity > p.quantity:
            raise ValueError(f"Not enough stock. Available: {p.quantity}")
        p.quantity -= quantity
        self.record_transaction(p.product_id, "OUT", quantity, None, user.username)
        self.save()
        return p

    def low_stock_products(self, user):
        self.check(user, "low_stock")
        return [p for p in self.products if p.active and p.is_low()]

    def get_history(self, user):
        if user.can("view_all_history"):
            return self.transactions
        self.check(user, "view_own_history")
        return [t for t in self.transactions if t.username == user.username]