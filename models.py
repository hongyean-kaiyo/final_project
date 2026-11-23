"""Data classes: Category, Supplier, Product, StockTransaction"""


class Category:
    def __init__(self, cat_id, name):
        self.cat_id = cat_id
        self.name = name

    def to_dict(self):
        return {"cat_id": self.cat_id, "name": self.name}


class Supplier:
    def __init__(self, supplier_id, name, contact, address):
        self.supplier_id = supplier_id
        self.name = name
        self.contact = contact
        self.address = address

    def to_dict(self):
        return {"supplier_id": self.supplier_id, "name": self.name,
                "contact": self.contact, "address": self.address}


class Product:
    def __init__(self, product_id, name, category_id, price, quantity,
                 shelf, min_stock=5, active=True):
        self.product_id = product_id
        self.name = name
        self.category_id = category_id
        self.price = price          # uses the setter below (validation)
        self.quantity = quantity    # uses the setter below (validation)
        self.shelf = shelf
        self.min_stock = min_stock
        self.active = active

    # Encapsulation: price and quantity are protected by rules
    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if value <= 0:
            raise ValueError("Price must be greater than zero.")
        self._price = value

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        if value < 0:
            raise ValueError("Quantity cannot be negative.")
        self._quantity = value

    def is_low(self):
        return self.quantity < self.min_stock

    def to_dict(self):
        return {"product_id": self.product_id, "name": self.name,
                "category_id": self.category_id, "price": self.price,
                "quantity": self.quantity, "shelf": self.shelf,
                "min_stock": self.min_stock, "active": self.active}


class StockTransaction:
    def __init__(self, tx_id, product_id, kind, quantity,
                 supplier_id, date, username):
        self.tx_id = tx_id
        self.product_id = product_id
        self.kind = kind              # "IN" or "OUT"
        self.quantity = quantity
        self.supplier_id = supplier_id
        self.date = date
        self.username = username

    def to_dict(self):
        return {"tx_id": self.tx_id, "product_id": self.product_id,
                "kind": self.kind, "quantity": self.quantity,
                "supplier_id": self.supplier_id, "date": self.date,
                "username": self.username}

