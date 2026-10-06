from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access: str
    refresh: str


class CategoryRead(BaseModel):
    id: int
    name: str
    description: str = ''

    class Config:
        from_attributes = True


class ProductRead(BaseModel):
    id: int
    name: str
    description: str = ''
    price: Decimal
    stock: int
    image: Optional[str] = None
    category: Optional[int] = Field(default=None, validation_alias='category_id')
    popularity: int = 0

    class Config:
        from_attributes = True


class CartItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_image: Optional[str] = None
    quantity: int
    price: Decimal

    class Config:
        from_attributes = True


class OrderStatusEventRead(BaseModel):
    id: int
    status: str
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    shipping_address: str = ''
    payment_method: Literal['cash_on_delivery', 'online', 'debit_card', 'credit_card'] = 'online'


class PaymentCreate(BaseModel):
    order_id: int


class OrderRead(BaseModel):
    id: int
    user_id: int
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    total: Decimal
    payment_status: str
    order_status: str
    payment_method: str = 'online'
    timestamp: Optional[datetime] = None
    shipping_address: str = ''
    tracking_number: str = ''
    carrier_name: str = 'SmartCart Express'
    shipped_at: Optional[datetime] = None
    estimated_delivery: Optional[date] = None
    items: list[OrderItemRead] = Field(default_factory=list)
    status_history: list['OrderStatusEventRead'] = Field(default_factory=list)

    class Config:
        from_attributes = True


class PaymentRead(BaseModel):
    id: int
    order_id: int
    amount: Decimal
    payment_method: str
    transaction_id: str
    status: str

    class Config:
        from_attributes = True


class NotificationRead(BaseModel):
    id: int
    user_id: int
    type: str
    message: str
    is_read: bool
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True
