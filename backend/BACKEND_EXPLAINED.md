# Backend Code Explained - Line by Line

A comprehensive guide to understanding every file in the e-commerce backend, the concepts involved, and how we built it step-by-step.

---

## Table of Contents

1. [Project Structure & Concepts](#project-structure--concepts)
2. [Configuration Files](#configuration-files)
3. [Core Layer](#core-layer)
4. [Database Models](#database-models)
5. [Pydantic Schemas](#pydantic-schemas)
6. [API Dependencies](#api-dependencies)
7. [API Endpoints](#api-endpoints)
8. [Main Application](#main-application)

---

## Project Structure & Concepts

### Architecture Pattern: Layered Architecture

```
┌─────────────────────────────────────┐
│   Client (Browser/Mobile/Tests)    │
└──────────────┬──────────────────────┘
               │ HTTP Requests
┌──────────────▼──────────────────────┐
│      API Layer (Endpoints)          │ ← Routes & Request Handling
├─────────────────────────────────────┤
│      Schemas (Pydantic)             │ ← Data Validation
├─────────────────────────────────────┤
│      Business Logic                 │ ← Processing & Rules
├─────────────────────────────────────┤
│      Models (SQLAlchemy)            │ ← Database Structure
├─────────────────────────────────────┤
│      Core (Config, Security, DB)    │ ← Foundation
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Database (PostgreSQL)          │
└─────────────────────────────────────┘
```

### Key Concepts Used

1. **Dependency Injection**: FastAPI's `Depends()` system
2. **Async/Await**: Non-blocking database operations
3. **ORM (Object-Relational Mapping)**: SQLAlchemy for database
4. **Data Validation**: Pydantic for request/response validation
5. **Authentication**: JWT (JSON Web Tokens)
6. **Password Security**: bcrypt hashing
7. **Database Migrations**: Alembic for schema changes

---

## Configuration Files

### 1. `pyproject.toml` - Dependency Management

**Purpose**: Defines project metadata and dependencies using Poetry

```toml
[tool.poetry]
name = "ecommerce-backend"              # Project name
version = "0.1.0"                       # Semantic versioning
description = "Modern E-commerce API"
authors = ["Your Name"]
package-mode = false                    # Not a library, it's an application

[tool.poetry.dependencies]
python = "^3.10"                        # Minimum Python version
fastapi = "^0.109.0"                    # Web framework
uvicorn = "^0.27.0"                     # ASGI server
sqlalchemy = {extras = ["asyncio"], version = "^2.0.25"}  # ORM with async support
psycopg = {extras = ["binary"], version = "^3.1.18"}      # PostgreSQL driver
pydantic = {extras = ["email"], version = "^2.5.3"}       # Data validation
pydantic-settings = "^2.1.0"            # Environment variable management
python-jose = {extras = ["cryptography"], version = "^3.3.0"}  # JWT tokens
bcrypt = "^4.0.1"                       # Password hashing
python-multipart = "^0.0.6"             # Form data parsing
redis = "^5.0.1"                        # Caching (future use)
```

**Concepts**:

- **Poetry**: Modern Python dependency manager (like npm for Node.js)
- **Extras**: Optional features (e.g., `[asyncio]` adds async support)
- **Version Constraints**: `^0.109.0` means "0.109.0 or higher, but less than 1.0.0"

---

## Core Layer

### 1. `app/core/config.py` - Application Settings

**Purpose**: Centralize all configuration using environment variables

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database connection string
    # Format: postgresql+psycopg://user:password@host:port/database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5433/ecommerce_db"

    # JWT Secret Key - MUST be changed in production!
    SECRET_KEY: str = "changethis_secret_key_for_dev"

    # JWT Algorithm for encoding/decoding tokens
    ALGORITHM: str = "HS256"

    # Token expiration time in minutes
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

# Create a single instance to use throughout the app
settings = Settings()
```

**Concepts**:

- **Environment Variables**: Configuration that changes between dev/staging/production
- **Pydantic Settings**: Automatically loads from `.env` files or environment
- **Singleton Pattern**: One `settings` instance shared everywhere
- **Default Values**: Fallback if environment variable not set

**Why This Matters**:

- Easy to change database without touching code
- Different settings for development vs production
- Secrets (like `SECRET_KEY`) not hardcoded in version control

---

### 2. `app/core/database.py` - Database Connection

**Purpose**: Set up SQLAlchemy for async database operations

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Create async database engine
# echo=True logs all SQL queries (useful for debugging)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

# Session factory - creates new database sessions
# expire_on_commit=False keeps objects accessible after commit
SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for all database models
Base = declarative_base()
```

**Concepts**:

- **Database Engine**: Connection pool manager
- **Session**: A "conversation" with the database
- **Session Factory**: Creates new sessions for each request
- **Declarative Base**: Parent class for all models (provides ORM magic)
- **Async Engine**: Non-blocking database operations

**Flow**:

1. Request comes in
2. Create a new session from `SessionLocal`
3. Use session to query/modify database
4. Commit changes
5. Close session

---

### 3. `app/core/security.py` - Authentication & Security

**Purpose**: Handle password hashing and JWT token generation

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from app.core.config import settings

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token for a user

    Args:
        subject: Usually the user's email
        expires_delta: How long until token expires

    Returns:
        Encoded JWT string
    """
    # Calculate expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    # Create payload (data inside the token)
    to_encode = {"exp": expire, "sub": str(subject)}

    # Encode using secret key
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain password matches the hashed version

    Args:
        plain_password: User's input
        hashed_password: Stored hash from database

    Returns:
        True if passwords match
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),      # Convert to bytes
        hashed_password.encode('utf-8')      # Convert to bytes
    )

def get_password_hash(password: str) -> str:
    """
    Hash a password for secure storage

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()                  # Generate random salt
    return bcrypt.hashpw(
        password.encode('utf-8'),            # Convert to bytes
        salt
    ).decode('utf-8')                        # Convert back to string
```

**Concepts**:

**JWT (JSON Web Token)**:

```
Header.Payload.Signature
eyJhbGc...  .  eyJzdWI...  .  SflKxwRJ...
```

- **Header**: Algorithm used (HS256)
- **Payload**: Data (user email, expiration)
- **Signature**: Proves token wasn't tampered with

**Password Hashing**:

```
Plain Password → bcrypt → Hash (stored in DB)
"password123" → "$2b$12$..." (60 characters)
```

- **Salt**: Random data added before hashing (prevents rainbow table attacks)
- **One-way**: Can't reverse hash to get original password
- **Slow**: Intentionally slow to prevent brute-force attacks

**Why This Matters**:

- Never store plain passwords
- Tokens allow stateless authentication (no session storage needed)
- Each token is self-contained and verifiable

---

## Database Models

### 1. `app/models/user.py` - User Model

**Purpose**: Define the structure of the users table

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from enum import Enum
from app.core.database import Base

# Enum for user roles
class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"                  # Table name in database

    # Primary key - auto-incrementing integer
    id = Column(Integer, primary_key=True, index=True)

    # User's full name - indexed for faster searches
    full_name = Column(String, index=True)

    # Email - must be unique, indexed, cannot be null
    email = Column(String, unique=True, index=True, nullable=False)

    # Hashed password - never store plain passwords!
    hashed_password = Column(String, nullable=False)

    # Account status - default to active
    is_active = Column(Boolean, default=True)

    # User role - default to customer
    role = Column(String, default=UserRole.CUSTOMER.value)

    # Timestamps - automatically set by database
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Concepts**:

**SQLAlchemy Column Types**:

- `Integer`: Whole numbers
- `String`: Text (VARCHAR in SQL)
- `Boolean`: True/False
- `DateTime`: Date and time with timezone

**Column Options**:

- `primary_key=True`: Unique identifier for each row
- `index=True`: Create database index for faster lookups
- `unique=True`: No two rows can have same value
- `nullable=False`: Field is required
- `default=value`: Value if not provided

**Timestamps**:

- `server_default=func.now()`: Database sets value on INSERT
- `onupdate=func.now()`: Database updates value on UPDATE

**Why Enums**:

```python
# Without Enum (error-prone)
user.role = "admon"  # Typo! No error until runtime

# With Enum (type-safe)
user.role = UserRole.ADMIN  # IDE autocomplete, compile-time checking
```

---

### 2. `app/models/product.py` - Product Model

```python
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    # Product details
    name = Column(String, index=True, nullable=False)
    description = Column(String)

    # Price stored as float (in production, use Decimal for exact values)
    price = Column(Float, nullable=False)

    # Stock quantity
    stock = Column(Integer, default=0)

    # Optional image URL
    image_url = Column(String)

    # Category for filtering
    category = Column(String, index=True)

    # Soft delete - hide instead of deleting
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Concepts**:

**Soft Delete**:

```python
# Hard delete (permanent)
db.delete(product)

# Soft delete (reversible)
product.is_active = False
```

- Preserves data for analytics
- Can restore if deleted by mistake
- Queries filter by `is_active=True`

**Indexing Strategy**:

- `name`: Searched frequently
- `category`: Used in filters
- `id`: Primary key (automatic index)

---

### 3. `app/models/cart.py` - Cart Models

```python
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to users table
    # unique=True: One cart per user
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship: Cart has many CartItems
    # cascade="all, delete-orphan": Delete items when cart is deleted
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    cart_id = Column(Integer, ForeignKey("carts.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    quantity = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship: CartItem belongs to Cart
    cart = relationship("Cart", back_populates="items")
```

**Concepts**:

**Foreign Keys**:

```
users table          carts table         cart_items table
┌────┬──────┐       ┌────┬─────────┐    ┌────┬─────────┬────────────┐
│ id │ name │       │ id │ user_id │    │ id │ cart_id │ product_id │
├────┼──────┤       ├────┼─────────┤    ├────┼─────────┼────────────┤
│ 1  │ John │◄──────┤ 1  │    1    │◄───┤ 1  │    1    │     5      │
│ 2  │ Jane │       │ 2  │    2    │    │ 2  │    1    │     7      │
└────┴──────┘       └────┴─────────┘    └────┴─────────┴────────────┘
```

**Relationships**:

```python
# One-to-Many
cart.items  # → [CartItem, CartItem, ...]

# Many-to-One
cart_item.cart  # → Cart object
```

**Cascade Delete**:

```python
db.delete(cart)
# Automatically deletes all cart.items
```

---

### 4. `app/models/order.py` - Order Models

```python
from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from app.core.database import Base

class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Order status workflow
    status = Column(String, default=OrderStatus.PENDING.value)

    # Total amount (calculated from items)
    total_amount = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to order items
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    quantity = Column(Integer, nullable=False)

    # Price at time of purchase (products prices may change later)
    price_at_purchase = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
```

**Concepts**:

**Order Status Workflow**:

```
PENDING → PAID → SHIPPED
   ↓
CANCELLED
```

**Price Snapshot**:

```python
# Product price changes over time
Product: $100 → $120 → $90

# Order preserves price at purchase
OrderItem.price_at_purchase = $100  # Never changes
```

**Why This Matters**:

- Historical accuracy for accounting
- Customer sees what they paid
- Analytics on price changes

---

## Pydantic Schemas

### Purpose of Schemas

**Models vs Schemas**:

```
SQLAlchemy Model (Database)    Pydantic Schema (API)
┌──────────────────┐          ┌──────────────────┐
│ User             │          │ UserResponse     │
│ - id             │          │ - id             │
│ - email          │          │ - email          │
│ - hashed_password│  ──X──►  │                  │ ← Password hidden!
│ - created_at     │          │ - created_at     │
└──────────────────┘          └──────────────────┘
```

### 1. `app/schemas/user.py` - User Schemas

```python
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole

# Shared properties across schemas
class UserBase(BaseModel):
    email: EmailStr                              # Validates email format
    full_name: Optional[str] = None              # Optional field
    is_active: Optional[bool] = True
    role: UserRole = UserRole.CUSTOMER           # Default role

# Schema for creating a user (includes password)
class UserCreate(UserBase):
    password: str                                # Plain password (will be hashed)

# Schema for updating a user
class UserUpdate(UserBase):
    password: Optional[str] = None               # Password is optional on update

# Schema for returning user data (no password!)
class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True                   # Allow ORM models to be converted
```

**Concepts**:

**Validation**:

```python
# EmailStr validates format
UserCreate(email="invalid")  # ❌ Raises ValidationError
UserCreate(email="user@example.com")  # ✅ Valid

# Type checking
UserCreate(email=123)  # ❌ Must be string
```

**Inheritance**:

```
UserBase (email, full_name, is_active, role)
    ↓
UserCreate (+ password)
UserUpdate (password optional)
UserResponse (+ id, created_at)
```

**Config.from_attributes**:

```python
# Convert SQLAlchemy model to Pydantic schema
user_model = db.query(User).first()
user_response = UserResponse.from_orm(user_model)
```

---

### 2. `app/schemas/product.py` - Product Schemas

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0
    image_url: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    pass                                         # Inherits all fields from ProductBase

class ProductUpdate(ProductBase):
    name: Optional[str] = None                   # All fields optional for partial updates
    price: Optional[float] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

**Concepts**:

**Partial Updates**:

```python
# Update only price
ProductUpdate(price=99.99)  # ✅ Valid

# Update multiple fields
ProductUpdate(price=99.99, stock=50)  # ✅ Valid
```

---

## API Dependencies

### `app/api/deps.py` - Dependency Injection

**Purpose**: Reusable functions that provide common functionality to endpoints

```python
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.user import User

# OAuth2 scheme - tells FastAPI where to look for the token
# tokenUrl: endpoint that provides tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_db() -> Generator:
    """
    Dependency that provides a database session

    Yields:
        AsyncSession: Database session

    Usage:
        @app.get("/users")
        async def get_users(db: Session = Depends(get_db)):
            ...
    """
    async with SessionLocal() as session:
        yield session                            # Provide session to endpoint
        # Session automatically closes after endpoint finishes

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency that gets the current authenticated user

    Args:
        db: Database session (injected)
        token: JWT token from Authorization header (injected)

    Returns:
        User: Current user object

    Raises:
        HTTPException: If token is invalid or user not found

    Usage:
        @app.get("/profile")
        async def get_profile(current_user: User = Depends(get_current_user)):
            return current_user
    """
    # Create exception for invalid credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Extract email from token
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Find user in database
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user
```

**Concepts**:

**Dependency Injection Flow**:

```
1. Request arrives: GET /profile
   Header: Authorization: Bearer eyJhbGc...

2. FastAPI sees: current_user: User = Depends(get_current_user)

3. Executes get_current_user:
   - Needs db → calls get_db()
   - Needs token → extracts from Authorization header

4. get_current_user returns User object

5. Endpoint receives User object in current_user parameter
```

**OAuth2PasswordBearer**:

```python
# Automatically extracts token from header
Authorization: Bearer <token>
                      ↑
                      Extracted and passed to oauth2_scheme
```

**Generator Pattern**:

```python
async def get_db():
    session = SessionLocal()
    try:
        yield session        # Pause here, give session to endpoint
    finally:
        await session.close()  # Always close, even if error
```

---

## API Endpoints

### 1. `app/api/v1/endpoints/auth.py` - Authentication

```python
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    OAuth2 compatible token login

    Request Body (form data):
        username: User's email
        password: Plain password

    Returns:
        {
            "access_token": "eyJhbGc...",
            "token_type": "bearer"
        }
    """
    # Find user by email (username field contains email)
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalars().first()

    # Verify user exists and password is correct
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Generate JWT token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.email,
            expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Create new user

    Request Body:
        {
            "email": "user@example.com",
            "password": "securepass123",
            "full_name": "John Doe",
            "role": "customer"
        }

    Returns:
        UserResponse (without password)
    """
    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == user_in.email))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )

    # Create new user
    user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),  # Hash password!
        full_name=user_in.full_name,
        role=user_in.role.value                                        # Extract enum value
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)  # Reload from DB to get id and timestamps

    return user
```

**Concepts**:

**OAuth2PasswordRequestForm**:

```python
# Standard OAuth2 form fields
{
    "username": "user@example.com",  # We use email as username
    "password": "plaintext"
}
```

**Authentication Flow**:

```
1. User sends email + password
2. Server finds user in database
3. Server verifies password hash
4. Server creates JWT token
5. Client stores token
6. Client sends token with future requests
```

**Why Hash Passwords**:

```python
# NEVER store plain passwords!
user.password = "password123"  # ❌ WRONG

# Always hash
user.hashed_password = security.get_password_hash("password123")  # ✅ CORRECT
# Result: "$2b$12$KIXxLV..."
```

---

### 2. `app/api/v1/endpoints/products.py` - Products

```python
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api import deps
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter()

@router.get("/", response_model=List[ProductResponse])
async def read_products(
    db: Session = Depends(deps.get_db),
    skip: int = 0,                               # Pagination offset
    limit: int = 100,                            # Pagination limit
    category: Optional[str] = None               # Optional filter
) -> Any:
    """
    Retrieve products with optional filtering

    Query Parameters:
        skip: Number of products to skip (default: 0)
        limit: Maximum products to return (default: 100)
        category: Filter by category (optional)

    Returns:
        List of products
    """
    # Build query
    query = select(Product).offset(skip).limit(limit)

    # Add category filter if provided
    if category:
        query = query.filter(Product.category == category)

    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=ProductResponse)
async def create_product(
    *,
    db: Session = Depends(deps.get_db),
    product_in: ProductCreate,
    current_user: User = Depends(deps.get_current_user),  # Requires authentication
) -> Any:
    """
    Create new product (Admin only)

    Request Body:
        {
            "name": "Gaming Laptop",
            "description": "High performance",
            "price": 1500.00,
            "stock": 10,
            "category": "Electronics"
        }

    Returns:
        Created product
    """
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Create product
    product = Product(
        name=product_in.name,
        description=product_in.description,
        price=product_in.price,
        stock=product_in.stock,
        image_url=product_in.image_url,
        category=product_in.category,
        is_active=product_in.is_active
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    return product

@router.get("/{product_id}", response_model=ProductResponse)
async def read_product_by_id(
    product_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get product by ID

    Path Parameters:
        product_id: Product ID

    Returns:
        Product details
    """
    result = await db.execute(select(Product).filter(Product.id == product_id))
    product = result.scalars().first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product
```

**Concepts**:

**Pagination**:

```python
# Request: GET /products?skip=0&limit=10
# Returns: Products 1-10

# Request: GET /products?skip=10&limit=10
# Returns: Products 11-20
```

**Authorization vs Authentication**:

```python
# Authentication: Who are you?
current_user: User = Depends(deps.get_current_user)

# Authorization: What can you do?
if current_user.role != UserRole.ADMIN:
    raise HTTPException(...)
```

---

### 3. `app/api/v1/endpoints/cart.py` - Shopping Cart

```python
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.api import deps
from app.models.user import User
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse

router = APIRouter()

async def get_or_create_cart(db: Session, user_id: int) -> Cart:
    """
    Helper function: Get user's cart or create if doesn't exist

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Cart object with items eagerly loaded
    """
    # Query with eager loading of items relationship
    result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.items))       # Load items in same query
        .filter(Cart.user_id == user_id)
    )
    cart = result.scalars().first()

    # Create cart if doesn't exist
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart, ["items"])       # Refresh with items

    return cart

@router.get("/", response_model=CartResponse)
async def get_cart(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user's cart

    Returns:
        {
            "id": 1,
            "user_id": 1,
            "items": [
                {"product_id": 5, "quantity": 2},
                {"product_id": 7, "quantity": 1}
            ]
        }
    """
    cart = await get_or_create_cart(db, current_user.id)
    return cart

@router.post("/items", response_model=CartResponse)
async def add_to_cart(
    *,
    db: Session = Depends(deps.get_db),
    item_in: CartItemCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Add item to cart or update quantity if already exists

    Request Body:
        {
            "product_id": 5,
            "quantity": 2
        }
    """
    # Verify product exists
    result = await db.execute(select(Product).filter(Product.id == item_in.product_id))
    product = result.scalars().first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get or create cart
    cart = await get_or_create_cart(db, current_user.id)

    # Check if item already in cart
    result = await db.execute(
        select(CartItem).filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == item_in.product_id
        )
    )
    cart_item = result.scalars().first()

    if cart_item:
        # Update existing item
        cart_item.quantity += item_in.quantity
    else:
        # Add new item
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=item_in.product_id,
            quantity=item_in.quantity
        )
        db.add(cart_item)

    await db.commit()
    await db.refresh(cart)

    return cart
```

**Concepts**:

**Eager Loading**:

```python
# Without selectinload (N+1 problem)
cart = db.query(Cart).first()
for item in cart.items:              # Separate query for EACH item!
    print(item.quantity)

# With selectinload (1 query)
cart = db.query(Cart).options(selectinload(Cart.items)).first()
for item in cart.items:              # Already loaded!
    print(item.quantity)
```

**Idempotent Operations**:

```python
# Adding same product twice
add_to_cart(product_id=5, quantity=2)  # Creates item with quantity=2
add_to_cart(product_id=5, quantity=3)  # Updates to quantity=5 (2+3)
```

---

### 4. `app/api/v1/endpoints/orders.py` - Order Processing

```python
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.api import deps
from app.models.user import User
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderResponse

router = APIRouter()

@router.post("/", response_model=OrderResponse)
async def create_order(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create order from user's cart

    Process:
        1. Get cart items
        2. Validate stock availability
        3. Calculate total
        4. Create order
        5. Deduct stock
        6. Clear cart

    Returns:
        Created order with items
    """
    # Get user's cart
    result = await db.execute(select(Cart).filter(Cart.user_id == current_user.id))
    cart = result.scalars().first()

    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Get cart items
    result = await db.execute(select(CartItem).filter(CartItem.cart_id == cart.id))
    cart_items = result.scalars().all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Validate stock and calculate total
    total_amount = 0.0
    order_items_data = []

    for cart_item in cart_items:
        # Get product
        result = await db.execute(select(Product).filter(Product.id == cart_item.product_id))
        product = result.scalars().first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {cart_item.product_id} not found"
            )

        # Check stock
        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. Available: {product.stock}"
            )

        # Calculate item total
        item_total = product.price * cart_item.quantity
        total_amount += item_total

        # Store for order creation
        order_items_data.append({
            "product_id": product.id,
            "quantity": cart_item.quantity,
            "price": product.price
        })

    # Create order
    order = Order(
        user_id=current_user.id,
        status=OrderStatus.PENDING,
        total_amount=total_amount
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Create order items and update stock
    for item_data in order_items_data:
        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            price_at_purchase=item_data["price"]
        )
        db.add(order_item)

        # Deduct stock
        result = await db.execute(select(Product).filter(Product.id == item_data["product_id"]))
        product = result.scalars().first()
        product.stock -= item_data["quantity"]

    # Clear cart
    for cart_item in cart_items:
        await db.delete(cart_item)

    await db.commit()
    await db.refresh(order, ["items"])

    return order
```

**Concepts**:

**Transaction Management**:

```python
# All or nothing - if any step fails, everything rolls back
try:
    order = Order(...)
    db.add(order)

    product.stock -= quantity

    await db.commit()              # Commits all changes
except Exception:
    await db.rollback()            # Undoes all changes
```

**Stock Management**:

```python
# Before order
Product: stock=10

# Order for 3 items
order_item.quantity = 3
product.stock -= 3                 # stock=7

# If order cancelled later
product.stock += 3                 # stock=10 (restore)
```

**Price Snapshot**:

```python
# Capture price at purchase time
order_item.price_at_purchase = product.price  # $100

# Even if product price changes later
product.price = $120

# Order still shows original price
order_item.price_at_purchase  # Still $100
```

---

## Main Application

### `app/main.py` - FastAPI Application

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router

# Create FastAPI application
app = FastAPI(
    title="Modern E-commerce API",
    version="0.1.0",
)

# CORS Middleware - allows frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],                         # In production: specific domains only
    allow_credentials=True,
    allow_methods=["*"],                         # Allow all HTTP methods
    allow_headers=["*"],                         # Allow all headers
)

# Include API router with /api/v1 prefix
app.include_router(api_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the E-commerce API"}

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

**Concepts**:

**CORS (Cross-Origin Resource Sharing)**:

```
Frontend (localhost:3000)  →  Backend (localhost:8000)
                              ↑
                              Without CORS: ❌ Blocked by browser
                              With CORS: ✅ Allowed
```

**API Versioning**:

```
/api/v1/products  ← Current version
/api/v2/products  ← Future version (breaking changes)
```

**Router Organization**:

```
main.py
  └── /api/v1 (api_router)
        ├── /auth (auth.router)
        ├── /products (products.router)
        ├── /cart (cart.router)
        └── /orders (orders.router)
```

---

## Development Progression

### How We Built This Step-by-Step

#### Phase 1: Foundation

1. **Set up project structure**
   - Created `pyproject.toml` with dependencies
   - Set up Docker Compose for PostgreSQL and Redis

2. **Core configuration**
   - Created `config.py` for settings
   - Created `database.py` for SQLAlchemy setup
   - Created `security.py` for password hashing and JWT

#### Phase 2: Database Layer

3. **Defined models**
   - Started with `User` model (authentication foundation)
   - Added `Product` model (catalog)
   - Added `Cart` and `CartItem` models (shopping)
   - Added `Order` and `OrderItem` models (checkout)

4. **Set up migrations**
   - Initialized Alembic
   - Created initial migration
   - Applied migration to create tables

#### Phase 3: API Layer

5. **Created schemas**
   - Pydantic schemas for validation
   - Separate schemas for Create/Update/Response

6. **Built dependencies**
   - `get_db()` for database sessions
   - `get_current_user()` for authentication

7. **Implemented endpoints**
   - Auth endpoints (register, login)
   - Product endpoints (CRUD)
   - Cart endpoints (add, update, remove)
   - Order endpoints (create, view history)

#### Phase 4: Testing & Refinement

8. **Fixed issues**
   - Python 3.13 bcrypt compatibility
   - SQLAlchemy relationship loading
   - Database field mismatches

9. **End-to-end testing**
   - Created comprehensive test script
   - Verified complete workflow

---

## Key Takeaways

### Design Patterns Used

1. **Repository Pattern**: Models separate from business logic
2. **Dependency Injection**: Reusable dependencies
3. **DTO Pattern**: Schemas for data transfer
4. **Factory Pattern**: Session factory for database connections

### Best Practices Followed

1. **Never store plain passwords** - Always hash
2. **Use environment variables** - Configuration flexibility
3. **Validate all inputs** - Pydantic schemas
4. **Use transactions** - Data consistency
5. **Eager load relationships** - Avoid N+1 queries
6. **Version your API** - `/api/v1` prefix
7. **Document your code** - Docstrings and comments

### Security Measures

1. **Password Hashing**: bcrypt with salt
2. **JWT Tokens**: Stateless authentication
3. **Role-Based Access**: Admin vs Customer
4. **Input Validation**: Pydantic prevents injection
5. **HTTPS Ready**: Secure in production

---

## Next Steps for Learning

1. **Add more features**:
   - Product reviews and ratings
   - Wishlist functionality
   - Order tracking and status updates
   - Payment integration

2. **Improve performance**:
   - Redis caching for products
   - Database indexing optimization
   - Query optimization

3. **Add testing**:
   - Unit tests with pytest
   - Integration tests
   - Load testing

4. **Deploy to production**:
   - Set up CI/CD pipeline
   - Configure Nginx
   - Use proper secrets management
   - Set up monitoring and logging

---

This guide covered every major file and concept in the backend. Use it as a reference as you continue building and learning!
