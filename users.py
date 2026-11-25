class User:
    ROLE_PERMISSIONS = {
        "admin": {"view_products", "add_product", "search_product", "low_stock"},
        "staff": {"view_products", "search_product", "low_stock"},
        "viewer": {"view_products"},
    }

    def __init__(self, username, password, role="viewer"):
        self.username = username
        self.password = password
        self.role = role.lower().strip()

    def can(self, permission):
        if self.role == "admin":
            return True
        allowed = self.ROLE_PERMISSIONS.get(self.role, {"view_products"})
        return permission in allowed