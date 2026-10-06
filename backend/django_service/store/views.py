from decimal import Decimal
import csv
from io import BytesIO
import uuid

from django.db import transaction
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from .models import Cart, Category, Notification, Order, OrderItem, Payment, Product, User
from .serializers import (
    CartSerializer,
    CategorySerializer,
    NotificationSerializer,
    OrderSerializer,
    PaymentSerializer,
    ProductSerializer,
    RegisterSerializer,
    UserSerializer,
)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def dashboard_metrics():
    paid_orders = Order.objects.filter(payment_status='paid')
    total_sales = paid_orders.aggregate(total=Sum('total'))['total'] or Decimal('0')
    top_products = OrderItem.objects.filter(order__payment_status='paid').values(
        'product_id', 'product__name'
    ).annotate(units_sold=Sum('quantity')).order_by('-units_sold')[:5]
    monthly_revenue = {}
    for timestamp, amount in paid_orders.values_list('timestamp', 'total'):
        month = timestamp.strftime('%Y-%m')
        monthly_revenue[month] = monthly_revenue.get(month, Decimal('0')) + amount
    low_stock_products = Product.objects.filter(stock__lte=5).order_by('stock')[:10]
    return {
        'total_sales': float(total_sales),
        'revenue': float(total_sales),
        'order_count': Order.objects.count(),
        'user_count': User.objects.count(),
        'top_products': [
            {'id': item['product_id'], 'name': item['product__name'], 'units_sold': item['units_sold']}
            for item in top_products
        ],
        'revenue_trends': [
            {'month': month, 'revenue': float(revenue)}
            for month, revenue in sorted(monthly_revenue.items())
        ],
        'low_stock_products': ProductSerializer(low_stock_products, many=True).data,
    }


class RegisterUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            payload = {'user': UserSerializer(user).data, 'token': get_tokens_for_user(user)}
            return Response(payload, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({'detail': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email=email).first()
        if user is None or not user.check_password(password):
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({
            'user': UserSerializer(user).data,
            'token': get_tokens_for_user(user),
        }, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class CategoryListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class ProductListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        queryset = Product.objects.select_related('category')
        query = request.query_params.get('q')
        category_id = request.query_params.get('category')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        sort = request.query_params.get('sort', 'popularity')

        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        sort_mapping = {
            'popularity': '-popularity',
            'price_asc': 'price',
            'price_desc': '-price',
            'newest': '-created_at',
        }
        queryset = queryset.order_by(sort_mapping.get(sort, '-popularity'))
        return Response(ProductSerializer(queryset, many=True).data)


class ProductDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        product = Product.objects.select_related('category').filter(pk=pk).first()
        if product is None:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductSerializer(product).data)


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        items = Cart.objects.filter(user=request.user).select_related('product')
        serializer = CartSerializer(items, many=True)
        subtotal = sum((item.product.price * item.quantity) for item in items)
        data = {
            'items': serializer.data,
            'subtotal': float(subtotal),
            'total': float(subtotal),
        }
        return Response(data)


class CartItemCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product')
        quantity = int(request.data.get('quantity', 1))
        if not product_id:
            return Response({'detail': 'Product is required.'}, status=status.HTTP_400_BAD_REQUEST)
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        if quantity <= 0:
            return Response({'detail': 'Quantity must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)
        if product.stock < quantity:
            return Response({'detail': 'Not enough stock available.'}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
        cart_item.quantity = cart_item.quantity + quantity if not created else quantity
        cart_item.save()
        return Response(CartSerializer(cart_item).data, status=status.HTTP_201_CREATED)


class CartItemUpdateDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        cart_item = Cart.objects.filter(pk=pk, user=request.user).first()
        if not cart_item:
            return Response({'detail': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)
        quantity = int(request.data.get('quantity', cart_item.quantity))
        if quantity <= 0:
            cart_item.delete()
            return Response({'detail': 'Cart item removed.'}, status=status.HTTP_200_OK)
        if cart_item.product.stock < quantity:
            return Response({'detail': 'Not enough stock available.'}, status=status.HTTP_400_BAD_REQUEST)
        cart_item.quantity = quantity
        cart_item.save()
        return Response(CartSerializer(cart_item).data)

    def delete(self, request, pk):
        cart_item = Cart.objects.filter(pk=pk, user=request.user).first()
        if not cart_item:
            return Response({'detail': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)
        cart_item.delete()
        return Response({'detail': 'Cart item removed.'}, status=status.HTTP_204_NO_CONTENT)


class OrderListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = (
            Order.objects.filter(user=request.user)
            .select_related('user')
            .prefetch_related('items__product', 'status_history', 'payments')
        )
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request):
        with transaction.atomic():
            payment_method = request.data.get('payment_method', 'online')
            valid_payment_methods = {value for value, _ in Payment.PAYMENT_METHOD_CHOICES}
            if payment_method not in valid_payment_methods:
                return Response({'detail': 'Invalid payment method.'}, status=status.HTTP_400_BAD_REQUEST)
            cart_items = list(Cart.objects.filter(user=request.user).select_related('product'))
            if not cart_items:
                return Response({'detail': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

            for item in cart_items:
                if item.product.stock < item.quantity:
                    return Response({'detail': f'Not enough stock for {item.product.name}.'}, status=status.HTTP_400_BAD_REQUEST)

            total = sum((item.product.price * item.quantity) for item in cart_items)
            order = Order.objects.create(
                user=request.user,
                total=total,
                payment_status='pending',
                order_status='order_placed',
                shipping_address=request.data.get('shipping_address', '').strip(),
            )

            for item in cart_items:
                OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
                item.product.stock -= item.quantity
                item.product.save(update_fields=['stock', 'updated_at'])

            Payment.objects.create(order=order, amount=total, payment_method=payment_method, status='pending')
            Cart.objects.filter(user=request.user).delete()
            order.refresh_from_db()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        order = (
            Order.objects.filter(pk=pk, user=request.user)
            .select_related('user')
            .prefetch_related('items__product', 'status_history', 'payments')
            .first()
        )
        if order is None:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)


class PaymentCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.filter(pk=order_id, user=request.user).first()
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        payment = Payment.objects.filter(order=order).first()
        if payment is None:
            return Response({'detail': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)
        if payment.payment_method == 'cash_on_delivery':
            return Response({'detail': 'Cash on Delivery is collected after delivery.'}, status=status.HTTP_400_BAD_REQUEST)
        payment.transaction_id = f'demo_{uuid.uuid4().hex}'
        payment.status = 'pending'
        payment.save(update_fields=['status', 'transaction_id'])
        return Response({**PaymentSerializer(payment).data, 'demo': True})


class PaymentConfirmView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        payment = Payment.objects.filter(order_id=order_id, order__user=request.user).first()
        if payment is None:
            return Response({'detail': 'Payment not found.'}, status=status.HTTP_404_NOT_FOUND)
        if payment.payment_method == 'cash_on_delivery':
            return Response({'detail': 'Cash on Delivery is collected after delivery.'}, status=status.HTTP_400_BAD_REQUEST)
        if not payment.transaction_id.startswith('demo_'):
            return Response({'detail': 'A valid payment session is required.'}, status=status.HTTP_400_BAD_REQUEST)
        payment.status = 'paid'
        payment.transaction_id = payment.transaction_id or f'confirm_{uuid.uuid4().hex[:12]}'
        payment.save(update_fields=['status', 'transaction_id'])
        payment.order.payment_status = 'paid'
        payment.order.order_status = 'payment_confirmed'
        payment.order.save(update_fields=['payment_status', 'order_status'])
        return Response(PaymentSerializer(payment).data)


class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        return Response(NotificationSerializer(notifications, many=True).data)


class NotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        notification = Notification.objects.filter(pk=pk, user=request.user).first()
        if notification is None:
            return Response({'detail': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data)


class AdminUserListView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by('-created_at')
        return Response(UserSerializer(users, many=True).data)

    def post(self, request):
        role = request.data.get('role', 'customer')
        if role not in {'admin', 'staff', 'customer'}:
            return Response({'detail': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        if not email or not password or not request.data.get('name'):
            return Response({'detail': 'Name, email, and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({'detail': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        user = User(
            email=email,
            username=email,
            name=request.data['name'],
            role=role,
            is_staff=role in {'admin', 'staff'},
            is_superuser=role == 'admin',
        )
        user.set_password(password)
        user.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        user = User.objects.filter(pk=request.data.get('id')).first()
        if not user:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        if 'name' in request.data:
            user.name = request.data['name']
        if 'email' in request.data:
            user.email = request.data['email'].strip().lower()
            user.username = user.email
        if 'role' in request.data:
            role = request.data['role']
            if role not in {'admin', 'staff', 'customer'}:
                return Response({'detail': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)
            user.role = role
            user.is_staff = role in {'admin', 'staff'}
            user.is_superuser = role == 'admin'
        if 'is_active' in request.data:
            user.is_active = bool(request.data['is_active'])
        user.save()
        return Response(UserSerializer(user).data)

    def delete(self, request):
        user = User.objects.filter(pk=request.data.get('id')).first()
        if not user:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminProductView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        products = Product.objects.select_related('category').all()
        return Response(ProductSerializer(products, many=True).data)

    def post(self, request):
        data = request.data.copy()
        serializer = ProductSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        product_id = request.data.get('id')
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        product_id = request.data.get('id')
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response({'detail': 'Product deleted.'}, status=status.HTTP_204_NO_CONTENT)


class AdminOrderListView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        orders = Order.objects.prefetch_related('items').all()
        return Response(OrderSerializer(orders, many=True).data)

    def patch(self, request):
        order_id = request.data.get('id')
        order = Order.objects.filter(pk=order_id).first()
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        order_status = request.data.get('order_status', order.order_status)
        payment_status = request.data.get('payment_status', order.payment_status)
        if order_status not in dict(Order.ORDER_STATUS_CHOICES) or payment_status not in dict(Order.PAYMENT_STATUS_CHOICES):
            return Response({'detail': 'Invalid order or payment status.'}, status=status.HTTP_400_BAD_REQUEST)
        order.order_status = order_status
        order.payment_status = payment_status
        order.save(update_fields=['order_status', 'payment_status'])
        return Response(OrderSerializer(order).data)


class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response(dashboard_metrics())


class AdminReportExportView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        report_format = request.query_params.get('export', 'csv').lower()
        metrics = dashboard_metrics()
        if report_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="smart-ecommerce-report.csv"'
            writer = csv.writer(response)
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total sales', metrics['total_sales']])
            writer.writerow(['Order count', metrics['order_count']])
            writer.writerow(['User count', metrics['user_count']])
            writer.writerow([])
            writer.writerow(['Top-selling product', 'Units sold'])
            writer.writerows([[item['name'], item['units_sold']] for item in metrics['top_products']])
            writer.writerow([])
            writer.writerow(['Month', 'Revenue'])
            writer.writerows([[item['month'], item['revenue']] for item in metrics['revenue_trends']])
            writer.writerow([])
            writer.writerow(['Low-stock product', 'Stock'])
            writer.writerows([[item['name'], item['stock']] for item in metrics['low_stock_products']])
            return response
        if report_format == 'pdf':
            buffer = BytesIO()
            document = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            rows = [['Product', 'Units sold']] + [[item['name'], item['units_sold']] for item in metrics['top_products']]
            table = Table(rows, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dce8e2')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#9aa59e')),
                ('PADDING', (0, 0), (-1, -1), 7),
            ]))
            story = [
                Paragraph('Smart E-Commerce Report', styles['Title']),
                Paragraph(f"Total sales: INR {metrics['total_sales']:.2f}", styles['BodyText']),
                Paragraph(f"Orders: {metrics['order_count']} | Users: {metrics['user_count']}", styles['BodyText']),
                Spacer(1, 14),
                Paragraph('Top-selling products', styles['Heading2']),
                table,
            ]
            document.build(story)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="smart-ecommerce-report.pdf"'
            return response
        return Response({'detail': 'Use export=csv or export=pdf.'}, status=status.HTTP_400_BAD_REQUEST)


def admin_reports_dashboard(request):
    metrics = dashboard_metrics()
    max_revenue = max((item['revenue'] for item in metrics['revenue_trends']), default=0) or 1
    for item in metrics['revenue_trends']:
        item['bar_width'] = round(item['revenue'] / max_revenue * 100)
    return render(request, 'admin/store_reports.html', metrics)
