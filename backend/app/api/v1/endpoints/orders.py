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
    Create order from user's cart.
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
    
    # Calculate total and verify stock
    total_amount = 0.0
    order_items_data = []
    
    for cart_item in cart_items:
        # Get product
        result = await db.execute(select(Product).filter(Product.id == cart_item.product_id))
        product = result.scalars().first()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {cart_item.product_id} not found")
        
        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. Available: {product.stock}"
            )
        
        item_total = product.price * cart_item.quantity
        total_amount += item_total
        
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
    
    # Create order items and update product stock
    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            price_at_purchase=item_data["price"]
        )
        db.add(order_item)
        
        # Update product stock
        result = await db.execute(select(Product).filter(Product.id == item_data["product_id"]))
        product = result.scalars().first()
        product.stock -= item_data["quantity"]
    
    # Clear cart
    for cart_item in cart_items:
        await db.delete(cart_item)
    
    await db.commit()
    await db.refresh(order, ["items"])
    return order

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get current user's orders.
    """
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .filter(Order.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get order by ID.
    """
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .filter(Order.id == order_id)
    )
    order = result.scalars().first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")
    
    return order
