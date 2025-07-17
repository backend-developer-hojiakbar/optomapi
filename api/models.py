from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import JSONField


class Role(models.Model):
    class Permission(models.TextChoices):
        VIEW_DASHBOARD = "view_dashboard", "Boshqaruv panelini ko'rish"
        USE_SALES_TERMINAL = "use_sales_terminal", "Savdo terminalidan foydalanish"
        VIEW_SALES_HISTORY = "view_sales_history", "Savdolar tarixini ko'rish"
        MANAGE_PRODUCTS = "manage_products", "Mahsulotlarni boshqarish"
        MANAGE_WAREHOUSE = "manage_warehouse", "Omborni boshqarish"
        MANAGE_CUSTOMERS = "manage_customers", "Mijozlarni boshqarish"
        MANAGE_SUPPLIERS = "manage_suppliers", "Yetkazib beruvchilarni boshqarish"
        VIEW_REPORTS = "view_reports", "Hisobotlarni ko'rish"
        MANAGE_SETTINGS = "manage_settings", "Sozlamalarni boshqarish"
        MANAGE_EMPLOYEES = "manage_employees", "Xodimlarni boshqarish"

    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    permissions = JSONField(default=list)

    def __str__(self):
        return self.name


# ========= BU QISM O'ZGARDI =========
class EmployeeManager(BaseUserManager):
    def create_user(self, phone, name=None, password=None, **extra_fields):
        if not phone:
            raise ValueError('Foydalanuvchida telefon raqami bo`lishi shart')

        user = self.model(phone=phone, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, name=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser is_staff=True bo`lishi kerak.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser is_superuser=True bo`lishi kerak.')

        admin_role, _ = Role.objects.get_or_create(
            id='role_admin',
            defaults={
                'name': 'Admin',
                'permissions': [p[0] for p in Role.Permission.choices]
            }
        )
        extra_fields.setdefault('role', admin_role)

        return self.create_user(phone, name, password, **extra_fields)


class Employee(AbstractBaseUser, PermissionsMixin):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='employees')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EmployeeManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    # ========= O'ZGARISH TUGADI =========

    def __str__(self):
        return self.name or self.phone

    @property
    def pin(self):
        return "PIN is write-only"


class Unit(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=50, unique=True)


class Product(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Aktiv'
        ARCHIVED = 'archived', 'Arxivlangan'

    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=100, null=True, blank=True, unique=True)
    unit = models.CharField(max_length=50)
    purchasePrice = models.DecimalField(max_digits=12, decimal_places=2)
    salePrice = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.FloatField()
    minStock = models.FloatField()
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Supplier(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    contactPerson = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255, null=True, blank=True)
    bankDetails = models.TextField(null=True, blank=True)


class Customer(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255, null=True, blank=True)
    debt = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class Sale(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    date = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    seller = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='sales')


class CartItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.FloatField()
    price = models.DecimalField(max_digits=12, decimal_places=2)


class SalePayment(models.Model):
    class PaymentType(models.TextChoices):
        CASH = 'naqd', 'Naqd'
        CARD = 'plastik', 'Plastik'
        TRANSFER = 'o\'tkazma', "O'tkazma"
        DEBT = 'nasiya', 'Nasiya'

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    type = models.CharField(max_length=10, choices=PaymentType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)


class DebtPayment(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='debt_payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    paymentType = models.CharField(max_length=10, choices=SalePayment.PaymentType.choices)


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        KIRIM = 'kirim', 'Kirim'
        CHIQIM = 'chiqim', 'Chiqim'
        SAVDO = 'savdo', 'Savdo'
        VOZVRAT = 'vozvrat', "Vozvrat"

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.FloatField()
    type = models.CharField(max_length=10, choices=MovementType.choices)
    date = models.DateTimeField(auto_now_add=True)
    relatedId = models.CharField(max_length=100, null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)


class GoodsReceipt(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    date = models.DateTimeField(auto_now_add=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    docNumber = models.CharField(max_length=100, null=True, blank=True)
    totalAmount = models.DecimalField(max_digits=14, decimal_places=2)


class GoodsReceiptItem(models.Model):
    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.FloatField()
    purchasePrice = models.DecimalField(max_digits=12, decimal_places=2)


class StoreSettings(models.Model):
    id = models.CharField(max_length=100, default="singleton", primary_key=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    currency = models.CharField(max_length=10)
    receiptHeader = models.TextField(null=True, blank=True)
    receiptFooter = models.TextField(null=True, blank=True)
    receiptShowStoreName = models.BooleanField(default=True)
    receiptShowAddress = models.BooleanField(default=True)
    receiptShowPhone = models.BooleanField(default=True)
    receiptShowChekId = models.BooleanField(default=True)
    receiptShowDate = models.BooleanField(default=True)
    receiptShowSeller = models.BooleanField(default=True)
    receiptShowCustomer = models.BooleanField(default=True)