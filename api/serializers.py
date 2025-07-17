from rest_framework import serializers
from django.db import transaction
from .models import *
import shortuuid


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'
        read_only_fields = ['id']

    def create(self, validated_data):
        validated_data['id'] = f"role_{shortuuid.random(length=8)}"
        return super().create(validated_data)


class EmployeeSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    roleId = serializers.CharField(write_only=True, source='role_id')
    pin = serializers.CharField(write_only=True, min_length=4, max_length=4, required=False, allow_blank=True)

    class Meta:
        model = Employee
        fields = ['id', 'name', 'phone', 'role', 'roleId', 'pin']
        read_only_fields = ['id']

    def create(self, validated_data):
        pin = validated_data.pop('pin', None)
        if not pin:
            raise serializers.ValidationError({"pin": "Yangi xodim uchun PIN majburiy."})
        role_id = validated_data.pop('role_id')
        role = Role.objects.get(id=role_id)
        user = Employee.objects.create_user(
            phone=validated_data['phone'],
            name=validated_data['name'],
            password=pin,
            role=role,
            id=f"emp_{shortuuid.random(length=8)}"
        )
        return user

    def update(self, instance, validated_data):
        pin = validated_data.pop('pin', None)
        if pin:
            instance.set_password(pin)
        if 'role_id' in validated_data:
            role_id = validated_data.pop('role_id')
            instance.role = Role.objects.get(id=role_id)
        instance = super().update(instance, validated_data)
        instance.save()
        return instance


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'name']
        read_only_fields = ['id']


class StoreSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreSettings
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['id'] = f"prod_{shortuuid.random(length=10)}"
        return super().create(validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['id']

    def create(self, validated_data):
        validated_data['id'] = f"cust_{shortuuid.random(length=8)}"
        return super().create(validated_data)


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'
        read_only_fields = ['id']

    def create(self, validated_data):
        validated_data['id'] = f"sup_{shortuuid.random(length=8)}"
        return super().create(validated_data)


class CartItemSerializer(serializers.ModelSerializer):
    productId = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product'
    )
    product = ProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['productId', 'product', 'quantity', 'price']


class SalePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalePayment
        fields = ['type', 'amount']


class SaleSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)
    payments = SalePaymentSerializer(many=True)
    seller = EmployeeSerializer(read_only=True)
    customer = CustomerSerializer(read_only=True)

    customerId = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source='customer',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Sale
        fields = ['id', 'date', 'items', 'subtotal', 'discount', 'total', 'payments', 'customerId', 'customer',
                  'seller']
        read_only_fields = ['id', 'date', 'seller', 'customer']

    # ========= BU METOD O'ZGARDI =========
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        payments_data = validated_data.pop('payments')

        # Savdo yaratishdan oldin mahsulot qoldig'ini tekshirish
        for item_data in items_data:
            product = item_data['product']
            if product.stock < item_data['quantity']:
                raise serializers.ValidationError(
                    f"'{product.name}' mahsuloti uchun omborda yetarli qoldiq yo'q. "
                    f"Mavjud: {product.stock}, So'ralyapti: {item_data['quantity']}"
                )

        with transaction.atomic():
            sale_id = f"sale_{shortuuid.random(length=12)}"
            sale = Sale.objects.create(id=sale_id, **validated_data)

            for item_data in items_data:
                CartItem.objects.create(sale=sale, **item_data)

                product = item_data['product']
                product.stock -= item_data['quantity']
                product.save()

            for payment_data in payments_data:
                SalePayment.objects.create(sale=sale, **payment_data)

            debt_payment = next((p for p in payments_data if p['type'] == 'nasiya'), None)
            if debt_payment and validated_data.get('customer'):
                customer = validated_data['customer']
                customer.debt += debt_payment['amount']
                customer.save()
            return sale
    # ========= O'ZGARISH TUGADI =========


class GoodsReceiptItemSerializer(serializers.ModelSerializer):
    productId = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    product = ProductSerializer(read_only=True)

    class Meta:
        model = GoodsReceiptItem
        fields = ['productId', 'product', 'quantity', 'purchasePrice']


class GoodsReceiptSerializer(serializers.ModelSerializer):
    items = GoodsReceiptItemSerializer(many=True)
    supplierId = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        source='supplier',
        write_only=True
    )
    supplier = SupplierSerializer(read_only=True)

    class Meta:
        model = GoodsReceipt
        fields = ['id', 'date', 'supplier', 'supplierId', 'docNumber', 'items', 'totalAmount']
        read_only_fields = ['id', 'date', 'supplier']

    def create(self, validated_data):
        with transaction.atomic():
            items_data = validated_data.pop('items')
            receipt_id = f"rcpt_{shortuuid.random(length=12)}"
            receipt = GoodsReceipt.objects.create(id=receipt_id, **validated_data)

            for item_data in items_data:
                GoodsReceiptItem.objects.create(receipt=receipt, **item_data)
                product = item_data['product']
                product.stock += item_data['quantity']
                product.purchasePrice = item_data['purchasePrice']
                product.save()

            return receipt


class DebtPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtPayment
        fields = ['customerId', 'amount', 'paymentType']
        extra_kwargs = {'customerId': {'source': 'customer_id'}}