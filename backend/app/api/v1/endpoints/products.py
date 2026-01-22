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
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None
) -> Any:
    """
    Retrieve products.
    """
    query = select(Product).offset(skip).limit(limit)
    if category:
        query = query.filter(Product.category == category)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=ProductResponse)
async def create_product(
    *,
    db: Session = Depends(deps.get_db),
    product_in: ProductCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new product. Only Admin can create products.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
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
    Get product by ID.
    """
    result = await db.execute(select(Product).filter(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
