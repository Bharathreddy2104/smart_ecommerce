from datetime import datetime, timedelta
from decimal import Decimal
from email.message import EmailMessage
import smtplib
from typing import Dict, List, Optional
import uuid

import stripe
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Cart, Category, Notification, Order, OrderItem, Payment, Product, User
from app.db.session import get_db
from app.schemas import (
    CartItemRead,
    CategoryRead,
    LoginRequest,
    NotificationRead,
    OrderRead,
    PaymentRead,
    ProductRead,
    Token,
    UserCreate,
    UserRead,
)

app = FastAPI(title='Smart E-Commerce API', version='1.0.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

pwd_context = CryptContext(schemes=['django_pbkdf2_sha256'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')
active_connections: Dict[int, List[WebSocket]] = {}


def send_email(recipient: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST:
        return
    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = settings.SMTP_FROM
    message['To'] = recipient
    message.set_content(body)
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5) as server:
            if settings.SMTP_USER:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
    except (OSError, smtplib.SMTPException):
        return


def stripe_test_mode_enabled() -> bool:
    key = settings.STRIPE_SECRET_KEY.strip()
    placeholders = ('your_key', 'placeholder', 'change_me', 'example')
    return key.startswith('sk_test_') and len(key) > 30 and not any(value in key.lower() for value in placeholders)


async def broadcast_notification(user_id: int, payload: dict) -> None:
    connections = active_connections.get(user_id, [])
    for connection in list(connections):
        try:
            await connection.send_json(payload)
        except WebSocketDisconnect:
            connections.remove(connection)


def add_notification(db: Session, user_id: int, notification_type: str, message: str, background_tasks: BackgroundTasks) -> None:
    notification = Notification(user_id=user_id, type=notification_type, message=message)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    background_tasks.add_task(broadcast_notification, user_id, {
        'id': notification.id,
        'type': notification.type,
        'message': notification.message,
        'timestamp': notification.timestamp.isoformat(),
    })


@app.get('/')
def root():
    return {'message': 'Smart E-Commerce FastAPI service is running.'}


@app.get('/api/auth/providers')
def auth_providers():
    def configured(value: str) -> bool:
        normalized = value.strip().lower()
        return bool(normalized) and not normalized.startswith('your-') and 'placeholder' not in normalized

    return {
        'google': configured(settings.GOOGLE_CLIENT_ID),
        'facebook': configured(settings.FACEBOOK_APP_ID),
        'auth0': configured(settings.AUTH0_DOMAIN) and configured(settings.AUTH0_AUDIENCE),
    }


def create_token(user: User) -> Token:
    jwt_secret = settings.FASTAPI_SECRET_KEY or settings.JWT_SECRET_KEY
    expires = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_payload = {
        'sub': user.email,
        'user_id': user.id,
        'role': user.role,
        'token_type': 'access',
        'jti': uuid.uuid4().hex,
        'exp': expires,
    }
    refresh_payload = {
        'sub': user.email,
        'user_id': user.id,
        'role': user.role,
        'token_type': 'refresh',
        'jti': uuid.uuid4().hex,
        'exp': datetime.utcnow() + timedelta(days=7),
    }
    access = jwt.encode(access_payload, jwt_secret, algorithm=settings.JWT_ALGORITHM)
    refresh = jwt.encode(refresh_payload, jwt_secret, algorithm=settings.JWT_ALGORITHM)
    return Token(access=access, refresh=refresh)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    jwt_secret = settings.FASTAPI_SECRET_KEY or settings.JWT_SECRET_KEY
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=[settings.JWT_ALGORITHM])
        if payload.get('token_type') not in (None, 'access'):
            raise credentials_exception
        email = payload.get('sub')
        user_id = payload.get('user_id')
        if email is None and user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_query = db.query(User)
    user = user_query.filter(User.email == email).first() if email else user_query.filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


@app.post('/api/auth/register', response_model=dict)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail='User already exists.')

    user = User(
        name=payload.name,
        email=payload.email.lower(),
        password=pwd_context.hash(payload.password),
        role='customer',
        username=payload.email.lower(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user)
    send_email(user.email, 'Welcome to Smart E-Commerce', f'Hi {user.name}, your account is ready.')
    return {'user': UserRead.model_validate(user).model_dump(), 'token': token.model_dump()}


@app.post('/api/auth/login', response_model=dict)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not pwd_context.verify(payload.password, user.password):
        raise HTTPException(status_code=401, detail='Invalid email or password.')
    token = create_token(user)
    return {'user': UserRead.model_validate(user).model_dump(), 'token': token.model_dump()}


@app.get('/api/auth/me', response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get('/api/categories', response_model=List[CategoryRead])
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return [CategoryRead.model_validate(category) for category in categories]


@app.get('/api/products', response_model=List[ProductRead])
def list_products(
    q: Optional[str] = None,
    category: Optional[int] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    sort: Optional[str] = 'popularity',
    db: Session = Depends(get_db),
):
    query = db.query(Product)
    if q:
        query = query.filter(or_(Product.name.ilike(f'%{q}%'), Product.description.ilike(f'%{q}%')))
    if category:
        query = query.filter(Product.category_id == category)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'newest':
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.popularity.desc())
    return [ProductRead.model_validate(item) for item in query.all()]


@app.get('/api/products/{product_id}', response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found.')
    return ProductRead.model_validate(product)


@app.get('/api/cart', response_model=dict)
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Cart).filter(Cart.user_id == current_user.id).all()
    item_data = []
    subtotal = Decimal('0')
    for item in items:
        subtotal += Decimal(item.quantity) * item.product.price
        item_data.append({
            'id': item.id,
            'product_id': item.product_id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'unit_price': item.product.price,
        })
    return {'items': item_data, 'subtotal': float(subtotal), 'total': float(subtotal)}


@app.post('/api/cart/items', response_model=dict)
def add_cart_item(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product_id = int(payload.get('product'))
    quantity = int(payload.get('quantity', 1))
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found.')
    if quantity <= 0:
        raise HTTPException(status_code=400, detail='Quantity must be greater than zero.')
    if product.stock < quantity:
        raise HTTPException(status_code=400, detail='Not enough stock available.')

    cart_item = db.query(Cart).filter(Cart.user_id == current_user.id, Cart.product_id == product_id).first()
    if cart_item:
        if product.stock < cart_item.quantity + quantity:
            raise HTTPException(status_code=400, detail='Not enough stock available.')
        cart_item.quantity += quantity
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.add(cart_item)
    db.commit(); db.refresh(cart_item)
    return {'id': cart_item.id, 'product_id': product_id, 'quantity': cart_item.quantity}


@app.put('/api/cart/items/{item_id}', response_model=dict)
def update_cart_item(item_id: int, payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(Cart).filter(Cart.id == item_id, Cart.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail='Cart item not found.')
    quantity = int(payload.get('quantity', item.quantity))
    if quantity <= 0:
        db.delete(item); db.commit(); return {'detail': 'Cart item removed.'}
    if item.product.stock < quantity:
        raise HTTPException(status_code=400, detail='Not enough stock available.')
    item.quantity = quantity
    db.commit(); db.refresh(item)
    return {'id': item.id, 'product_id': item.product_id, 'quantity': item.quantity}


@app.delete('/api/cart/items/{item_id}')
def delete_cart_item(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(Cart).filter(Cart.id == item_id, Cart.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail='Cart item not found.')
    db.delete(item)
    db.commit()
    return {'detail': 'Cart item removed.'}


@app.post('/api/orders', response_model=OrderRead)
def create_order(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail='Cart is empty.')

    total = Decimal('0')
    for item in cart_items:
        if item.product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f'Not enough stock for {item.product.name}.')
        total += Decimal(item.quantity) * item.product.price

    order = Order(user_id=current_user.id, total=total, payment_status='pending', order_status='pending')
    db.add(order)
    db.commit(); db.refresh(order)

    for item in cart_items:
        order_item = OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity, price=item.product.price)
        db.add(order_item)
        item.product.stock -= item.quantity

    db.add(Payment(order_id=order.id, amount=total, payment_method='stripe', status='pending'))
    db.query(Cart).filter(Cart.user_id == current_user.id).delete()
    db.commit()
    db.refresh(order)
    add_notification(db, current_user.id, 'order', f'Order #{order.id} was placed.', background_tasks)
    background_tasks.add_task(send_email, current_user.email, 'Order received', f'Order #{order.id} total: {order.total}.')
    return OrderRead.model_validate(order)


@app.get('/api/orders', response_model=List[OrderRead])
def list_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == current_user.id).all()
    return [OrderRead.model_validate(order) for order in orders]


@app.get('/api/orders/{order_id}', response_model=OrderRead)
def get_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found.')
    return OrderRead.model_validate(order)


@app.post('/api/payments/create', response_model=dict)
def create_payment(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order_id = int(payload.get('order_id'))
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found.')
    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    stripe_key = settings.STRIPE_SECRET_KEY
    stripe_enabled = stripe_test_mode_enabled()
    if stripe_enabled:
        try:
            session = stripe.checkout.Session.create(
                mode='payment',
                line_items=[{
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {'name': f'Order #{order.id}'},
                        'unit_amount': int(order.total * 100),
                    },
                    'quantity': 1,
                }],
                success_url=f'{settings.FRONTEND_BASE_URL}/checkout?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'{settings.FRONTEND_BASE_URL}/checkout?cancelled=1',
                metadata={'order_id': str(order.id), 'user_id': str(current_user.id)},
                api_key=stripe_key,
            )
        except stripe.StripeError:
            raise HTTPException(status_code=502, detail='Stripe test checkout could not be created.')
        if payment is None:
            payment = Payment(order_id=order.id, amount=order.total)
            db.add(payment)
        payment.payment_method = 'stripe'
        payment.transaction_id = session.id
        payment.status = 'pending'
        db.commit()
        db.refresh(payment)
        result = PaymentRead.model_validate(payment).model_dump()
        return {**result, 'checkout_url': session.url, 'demo': False}

    if payment is None:
        payment = Payment(order_id=order.id, amount=order.total, payment_method='mock', status='pending')
        db.add(payment)
    payment.payment_method = 'mock'
    payment.status = 'pending'
    db.commit()
    db.refresh(payment)
    result = PaymentRead.model_validate(payment).model_dump()
    return {**result, 'checkout_url': None, 'demo': True}


@app.post('/api/payments/confirm', response_model=PaymentRead)
def confirm_payment(payload: dict, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order_id = int(payload.get('order_id'))
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found.')
    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if not payment:
        raise HTTPException(status_code=404, detail='Payment not found.')
    session_id = payload.get('session_id')
    stripe_key = settings.STRIPE_SECRET_KEY
    stripe_enabled = stripe_test_mode_enabled()
    if stripe_enabled:
        if not session_id or session_id != payment.transaction_id:
            raise HTTPException(status_code=400, detail='A valid Stripe Checkout session is required.')
        try:
            session = stripe.checkout.Session.retrieve(session_id, api_key=stripe_key)
        except stripe.StripeError:
            raise HTTPException(status_code=400, detail='Stripe Checkout session could not be verified.')
        if session.payment_status != 'paid':
            raise HTTPException(status_code=400, detail='Stripe payment is not complete.')
    elif payment.payment_method != 'mock':
        raise HTTPException(status_code=400, detail='Payment cannot be confirmed in demo mode.')
    payment.status = 'paid'
    order.payment_status = 'paid'
    order.order_status = 'confirmed'
    db.commit()
    add_notification(db, current_user.id, 'payment', f'Payment confirmed for order #{order.id}.', background_tasks)
    background_tasks.add_task(send_email, current_user.email, 'Payment confirmed', f'Payment for order #{order.id} was confirmed.')
    return PaymentRead.model_validate(payment)


@app.post('/api/payments/webhook')
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail='Stripe webhook is not configured.')
    signature = request.headers.get('stripe-signature', '')
    try:
        event = stripe.Webhook.construct_event(await request.body(), signature, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(status_code=400, detail='Invalid Stripe webhook.')
    if event.type == 'checkout.session.completed':
        session = event.data.object
        payment = db.query(Payment).filter(Payment.transaction_id == session.id).first()
        if payment and session.payment_status == 'paid':
            order = db.query(Order).filter(Order.id == payment.order_id).first()
            payment.status = 'paid'
            order.payment_status = 'paid'
            order.order_status = 'confirmed'
            db.commit()
            add_notification(db, order.user_id, 'payment', f'Payment confirmed for order #{order.id}.', background_tasks)
            background_tasks.add_task(send_email, order.user.email, 'Payment confirmed', f'Payment for order #{order.id} was confirmed.')
    return {'received': True}


@app.get('/api/notifications', response_model=List[NotificationRead])
def list_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(Notification.user_id == current_user.id).all()
    return [NotificationRead.model_validate(n) for n in notifications]


@app.put('/api/notifications/{notification_id}/read', response_model=NotificationRead)
def mark_notification_read(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if not notification:
        raise HTTPException(status_code=404, detail='Notification not found.')
    notification.is_read = True
    db.commit(); db.refresh(notification)
    return NotificationRead.model_validate(notification)


@app.websocket('/ws/notifications')
async def notifications_socket(websocket: WebSocket):
    token = websocket.query_params.get('token')
    if not token:
        await websocket.close(code=4401)
        return
    try:
        payload = jwt.decode(token, settings.FASTAPI_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get('token_type') not in (None, 'access'):
            await websocket.close(code=4401)
            return
        email = payload.get('sub')
        user_id = payload.get('user_id')
    except JWTError:
        await websocket.close(code=4401)
        return
    db = next(get_db())
    user_query = db.query(User)
    user = user_query.filter(User.email == email).first() if email else user_query.filter(User.id == user_id).first()
    db.close()
    if user is None:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    active_connections.setdefault(user.id, []).append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections = active_connections.get(user.id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            active_connections.pop(user.id, None)
