from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = 'store_user'

    id = Column(Integer, primary_key=True, index=True)
    password = Column(String(128), nullable=False)
    last_login = Column(DateTime, nullable=True)
    is_superuser = Column(Boolean, default=False)
    username = Column(String(150), nullable=True, default='')
    first_name = Column(String(150), default='')
    last_name = Column(String(150), default='')
    email = Column(String(254), unique=True, nullable=False, index=True)
    is_staff = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    date_joined = Column(DateTime, default=datetime.utcnow)
    name = Column(String(150), nullable=False)
    role = Column(String(20), default='customer')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notifications = relationship('Notification', back_populates='user')
    cart_items = relationship('Cart', back_populates='user')
    orders = relationship('Order', back_populates='user')


class Category(Base):
    __tablename__ = 'store_category'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, default='')

    products = relationship('Product', back_populates='category')


class Product(Base):
    __tablename__ = 'store_product'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default='')
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    image = Column(String(255), nullable=True)
    category_id = Column(Integer, ForeignKey('store_category.id'), nullable=True)
    popularity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship('Category', back_populates='products')
    cart_items = relationship('Cart', back_populates='product')
    order_items = relationship('OrderItem', back_populates='product')


class Cart(Base):
    __tablename__ = 'store_cart'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('store_user.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('store_product.id'), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='cart_items')
    product = relationship('Product', back_populates='cart_items')


class Order(Base):
    __tablename__ = 'store_order'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('store_user.id'), nullable=False)
    total = Column(Numeric(12, 2), default=0)
    payment_status = Column(String(20), default='pending')
    order_status = Column(String(20), default='pending')
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order')
    payments = relationship('Payment', back_populates='order')


class OrderItem(Base):
    __tablename__ = 'store_order_item'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('store_order.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('store_product.id'), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Numeric(10, 2), nullable=False)

    order = relationship('Order', back_populates='items')
    product = relationship('Product', back_populates='order_items')


class Payment(Base):
    __tablename__ = 'store_payment'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('store_order.id'), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(20), default='stripe')
    transaction_id = Column(String(150), default='')
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship('Order', back_populates='payments')


class Notification(Base):
    __tablename__ = 'store_notification'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('store_user.id'), nullable=False)
    type = Column(String(20), default='system')
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='notifications')
