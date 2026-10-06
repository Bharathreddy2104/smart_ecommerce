from django.contrib.auth.models import AbstractUser, BaseUserManager
from datetime import timedelta
from django.db import models, transaction
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('customer', 'Customer'),
    ]

    username = models.CharField(max_length=150, blank=True, null=True, default='')
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    class Meta:
        db_table = 'store_user'

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'store_category'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    popularity = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'store_product'
        indexes = [models.Index(fields=['category', 'popularity'])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'store_cart'
        unique_together = ('user', 'product')

    def __str__(self):
        return f'{self.user.email} - {self.product.name}'

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('order_placed', 'Order Placed'),
        ('payment_confirmed', 'Payment Confirmed'),
        ('order_confirmed', 'Order Confirmed'),
        ('processing', 'Processing'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('payment_failed', 'Payment Failed'),
        ('return_requested', 'Return Requested'),
        ('returned', 'Returned'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    order_status = models.CharField(max_length=30, choices=ORDER_STATUS_CHOICES, default='order_placed')
    timestamp = models.DateTimeField(default=timezone.now)
    shipping_address = models.TextField(blank=True, default='')
    tracking_number = models.CharField(max_length=40, blank=True, default='')
    carrier_name = models.CharField(max_length=100, blank=True, default='SmartCart Express')
    shipped_at = models.DateTimeField(null=True, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'store_order'
        ordering = ['-timestamp']

    def __str__(self):
        return f'Order #{self.pk}'

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        previous_status = None
        if not is_new:
            previous_status = (
                Order.objects.filter(pk=self.pk)
                .values_list('order_status', flat=True)
                .first()
            )

        if not self.estimated_delivery:
            self.estimated_delivery = (self.timestamp or timezone.now()).date() + timedelta(days=5)
        if self.order_status in {'shipped', 'out_for_delivery', 'delivered'}:
            self.tracking_number = self.tracking_number or f'SC{self.pk or 0:09d}'
            self.shipped_at = self.shipped_at or timezone.now()
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'tracking_number', 'shipped_at'}
        if not is_new and previous_status != self.order_status and kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'estimated_delivery'}

        with transaction.atomic():
            super().save(*args, **kwargs)

            if is_new:
                OrderStatusEvent.objects.create(order=self, status=self.order_status)
                Notification.objects.create(
                    user=self.user,
                    type='order',
                    message=f'Your order #{self.pk} has been placed.',
                )
            elif previous_status != self.order_status:
                progression = [status for status, _ in self.ORDER_STATUS_CHOICES[:8]]
                previous_index = progression.index(previous_status) if previous_status in progression else -1
                current_index = progression.index(self.order_status) if self.order_status in progression else -1
                statuses_to_record = (
                    progression[previous_index + 1:current_index + 1]
                    if previous_index >= 0 and current_index > previous_index
                    else [self.order_status]
                )
                for status_value in statuses_to_record:
                    OrderStatusEvent.objects.create(order=self, status=status_value)
                    label = dict(self.ORDER_STATUS_CHOICES)[status_value]
                    notification_type = 'shipping' if status_value in {'shipped', 'out_for_delivery', 'delivered'} else 'order'
                    Notification.objects.create(
                        user=self.user,
                        type=notification_type,
                        message=f'Your order #{self.pk} {self._status_notification_text(status_value, label)}',
                    )

    @staticmethod
    def _status_notification_text(status_value, label):
        notification_text = {
            'order_placed': 'has been placed.',
            'payment_confirmed': 'has confirmed payment.',
            'order_confirmed': 'has been confirmed.',
            'processing': 'is being processed.',
            'packed': 'has been packed.',
            'shipped': 'has been shipped.',
            'out_for_delivery': 'is out for delivery.',
            'delivered': 'has been delivered.',
            'cancelled': 'has been cancelled.',
            'payment_failed': 'has a failed payment.',
            'return_requested': 'has a return request.',
            'returned': 'has been returned.',
        }
        return notification_text.get(status_value, f'has been updated to {label.lower()}.')


class OrderStatusEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=30, choices=Order.ORDER_STATUS_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'store_order_status_event'
        ordering = ['timestamp', 'id']

    def __str__(self):
        return f'Order #{self.order_id} - {self.get_status_display()}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'store_order_item'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash_on_delivery', 'Cash on Delivery'),
        ('online', 'Online Payment'),
        ('debit_card', 'Debit Card'),
        ('credit_card', 'Credit Card'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='online')
    transaction_id = models.CharField(max_length=150, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'store_payment'

    def __str__(self):
        return f'{self.order_id} - {self.status}'


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order', 'Order'),
        ('payment', 'Payment'),
        ('shipping', 'Shipping'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'store_notification'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user.email} - {self.type}'
