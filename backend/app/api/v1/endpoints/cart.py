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
    """Get user's cart or create if doesn't exist"""
    result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.items))
        .filter(Cart.user_id == user_id)
    )
    cart = result.scalars().first()
    
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart, ["items"])
    
    return cart

@router.get("/", response_model=CartResponse)
async def get_cart(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user's cart with all items.
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
    Add item to cart or update quantity if already exists.
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
        # Update quantity
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

@router.put("/items/{product_id}", response_model=CartResponse)
async def update_cart_item(
    *,
    db: Session = Depends(deps.get_db),
    product_id: int,
    item_in: CartItemUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update cart item quantity.
    """
    cart = await get_or_create_cart(db, current_user.id)
    
    result = await db.execute(
        select(CartItem).filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        )
    )
    cart_item = result.scalars().first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item not in cart")
    
    if item_in.quantity <= 0:
        await db.delete(cart_item)
    else:
        cart_item.quantity = item_in.quantity
    
    await db.commit()
    await db.refresh(cart)
    return cart

@router.delete("/items/{product_id}", response_model=CartResponse)
async def remove_from_cart(
    *,
    db: Session = Depends(deps.get_db),
    product_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Remove item from cart.
    """
    cart = await get_or_create_cart(db, current_user.id)
    
    result = await db.execute(
        select(CartItem).filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        )
    )
    cart_item = result.scalars().first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item not in cart")
    
    await db.delete(cart_item)
    await db.commit()
    await db.refresh(cart)
    return cart

@router.delete("/", response_model=CartResponse)
async def clear_cart(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Clear all items from cart.
    """
    cart = await get_or_create_cart(db, current_user.id)
    
    # Delete all items
    result = await db.execute(select(CartItem).filter(CartItem.cart_id == cart.id))
    items = result.scalars().all()
    for item in items:
        await db.delete(item)
    
    await db.commit()
    await db.refresh(cart)
    return cart
