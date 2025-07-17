from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *


# Admin panelini yanada qulay qilish uchun maxsus sozlamalar
class EmployeeAdmin(BaseUserAdmin):
    # Foydalanuvchi ro'yxatida ko'rinadigan ustunlar
    list_display = ('phone', 'name', 'role', 'is_staff', 'is_active')
    # Ro'yxatni filtrlash uchun maydonlar
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'role')
    # Qidiruv maydonlari
    search_fields = ('phone', 'name')
    # Tartiblash
    ordering = ('phone',)

    # Foydalanuvchini tahrirlash sahifasidagi maydonlar tartibi
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal info', {'fields': ('name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    # Yangi foydalanuvchi yaratish sahifasidagi maydonlar
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'name', 'role', 'password'),
        }),
    )
    readonly_fields = ('last_login', 'created_at', 'updated_at')


class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'permission_count')
    search_fields = ('name',)

    def permission_count(self, obj):
        return len(obj.permissions)

    permission_count.short_description = 'Ruxsatlar Soni'


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'salePrice', 'purchasePrice', 'stock', 'minStock', 'status')
    list_filter = ('status', 'unit')
    search_fields = ('name', 'barcode')
    ordering = ('name',)


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'debt')
    search_fields = ('name', 'phone')
    ordering = ('name',)


class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'contactPerson')
    search_fields = ('name', 'contactPerson')
    ordering = ('name',)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')


class SalePaymentInline(admin.TabularInline):
    model = SalePayment
    extra = 0
    readonly_fields = ('type', 'amount')


class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'customer', 'seller', 'total')
    list_filter = ('date', 'seller', 'customer')
    search_fields = ('id', 'customer__name', 'seller__name')
    readonly_fields = ('date', 'id', 'subtotal', 'discount', 'total')
    inlines = [CartItemInline, SalePaymentInline]


class GoodsReceiptItemInline(admin.TabularInline):
    model = GoodsReceiptItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'purchasePrice')


class GoodsReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'supplier', 'totalAmount')
    list_filter = ('date', 'supplier')
    search_fields = ('id', 'docNumber', 'supplier__name')
    readonly_fields = ('date', 'id', 'totalAmount')
    inlines = [GoodsReceiptItemInline]


class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    search_fields = ('name',)


# Modellarni admin panelida ro'yxatdan o'tkazish
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(GoodsReceipt, GoodsReceiptAdmin)
admin.site.register(Unit, UnitAdmin)

# Bu modellarni ham oddiy ko'rinishda ro'yxatdan o'tkazamiz
admin.site.register(StoreSettings)
admin.site.register(DebtPayment)
admin.site.register(StockMovement)