from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import Cart, Category, Notification, Order, OrderItem, OrderStatusEvent, Payment, Product, User


class StoreUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'name', 'role')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.is_staff = user.role in {'admin', 'staff'}
        user.is_superuser = user.role == 'admin'
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = StoreUserCreationForm
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'name', 'role', 'password1', 'password2')}),)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ['email', 'name', 'role', 'is_staff', 'is_active']
    search_fields = ['email', 'name']
    list_filter = ['role', 'is_staff', 'is_active']
    ordering = ['email']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'popularity']
    search_fields = ['name', 'description']
    list_filter = ['category']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity']
    search_fields = ['user__email', 'product__name']


class OrderStatusEventInline(admin.TabularInline):
    model = OrderStatusEvent
    extra = 0
    can_delete = False
    readonly_fields = ['status', 'timestamp']
    fields = ['status', 'timestamp']

    def has_add_permission(self, request, obj=None):
        return False


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ['product', 'quantity', 'price']
    fields = ['product', 'quantity', 'price']

    def has_add_permission(self, request, obj=None):
        return False


class PaymentAdminForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        order = cleaned_data.get('order')
        payment_method = cleaned_data.get('payment_method')
        payment_status = cleaned_data.get('status')
        if (
            order
            and payment_method == 'cash_on_delivery'
            and payment_status == 'paid'
            and order.order_status != 'delivered'
        ):
            raise forms.ValidationError('Cash on Delivery can be marked paid after the order is delivered.')
        return cleaned_data


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total', 'order_status', 'payment_status', 'tracking_number', 'estimated_delivery', 'timestamp']
    search_fields = ['user__email', 'user__name', 'id', 'tracking_number']
    list_filter = ['order_status', 'payment_status']
    readonly_fields = ['timestamp', 'shipped_at', 'payment_status']
    fieldsets = (
        ('Order', {'fields': ('user', 'total', 'payment_status', 'order_status', 'timestamp')}),
        ('Shipping', {'fields': ('shipping_address', 'carrier_name', 'tracking_number', 'shipped_at', 'estimated_delivery')}),
    )
    inlines = [OrderItemInline, OrderStatusEventInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    search_fields = ['product__name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    form = PaymentAdminForm
    list_display = ['order', 'customer', 'amount', 'payment_method', 'status', 'transaction_id', 'created_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['order__id', 'order__user__email', 'transaction_id']
    readonly_fields = ['transaction_id', 'created_at']

    @admin.display(description='Customer', ordering='order__user__email')
    def customer(self, obj):
        return obj.order.user.email

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.order.payment_status != obj.status:
            obj.order.payment_status = obj.status
            obj.order.save(update_fields=['payment_status'])


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'is_read', 'timestamp']
    list_filter = ['type', 'is_read']
