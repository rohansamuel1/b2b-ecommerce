import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_role
from app.database import get_db

router = APIRouter(tags=["Catalog Experience"])


def product_payload(product: models.Product):
    review_count = len(product.reviews)
    return {
        "id": product.id, "name": product.name, "description": product.description,
        "sku": product.sku, "price": product.price, "image_url": product.image_url,
        "vendor_id": product.vendor_id, "category_id": product.category_id,
        "category": product.category.name if product.category else None,
        "brand": product.brand, "rating": product.rating or 0,
        "review_count": review_count, "stock_quantity": product.stock_quantity,
        "reorder_level": product.reorder_level,
        "attributes": json.loads(product.attributes_json or "{}"),
    }


@router.get("/catalog/search")
def search_catalog(
    q: str = "", category_id: int | None = None, brand: str | None = None,
    min_price: float | None = None, max_price: float | None = None,
    min_rating: float | None = None, in_stock: bool = False,
    sort: str = Query("relevance", pattern="^(relevance|price_asc|price_desc|rating|newest)$"),
    limit: int = Query(24, ge=1, le=100), db: Session = Depends(get_db),
):
    query = db.query(models.Product)
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(or_(models.Product.name.ilike(term), models.Product.description.ilike(term), models.Product.sku.ilike(term), models.Product.brand.ilike(term)))
    if category_id: query = query.filter(models.Product.category_id == category_id)
    if brand: query = query.filter(models.Product.brand.ilike(brand))
    if min_price is not None: query = query.filter(models.Product.price >= min_price)
    if max_price is not None: query = query.filter(models.Product.price <= max_price)
    if min_rating is not None: query = query.filter(models.Product.rating >= min_rating)
    if in_stock: query = query.join(models.Inventory).filter(models.Inventory.stock_quantity > 0)
    order = {"price_asc": models.Product.price.asc(), "price_desc": models.Product.price.desc(), "rating": models.Product.rating.desc(), "newest": models.Product.id.desc()}.get(sort, models.Product.name.asc())
    products = query.order_by(order).limit(limit).all()
    return {"query": q, "count": len(products), "products": [product_payload(p) for p in products]}


@router.post("/categories", response_model=schemas.CategoryOut)
def create_category(payload: schemas.CategoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_role(["admin"]))):
    if db.query(models.Category).filter(func.lower(models.Category.name) == payload.name.lower()).first():
        raise HTTPException(409, "Category already exists")
    item = models.Category(**payload.model_dump()); db.add(item); db.commit(); db.refresh(item); return item


@router.get("/categories", response_model=list[schemas.CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).order_by(models.Category.name).all()


@router.get("/wishlist")
def get_wishlist(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    items = db.query(models.WishlistItem).filter(models.WishlistItem.user_id == current_user.id).order_by(models.WishlistItem.created_at.desc()).all()
    return [{"id": x.id, "created_at": x.created_at, "product": product_payload(x.product)} for x in items]


@router.post("/wishlist")
def add_wishlist(payload: schemas.WishlistCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not db.query(models.Product).filter(models.Product.id == payload.product_id).first(): raise HTTPException(404, "Product not found")
    item = db.query(models.WishlistItem).filter_by(user_id=current_user.id, product_id=payload.product_id).first()
    if not item: item = models.WishlistItem(user_id=current_user.id, product_id=payload.product_id); db.add(item); db.commit(); db.refresh(item)
    return {"id": item.id, "product_id": item.product_id}


@router.delete("/wishlist/{product_id}", status_code=204)
def remove_wishlist(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.WishlistItem).filter_by(user_id=current_user.id, product_id=product_id).first()
    if item: db.delete(item); db.commit()


@router.get("/products/{product_id}/reviews")
def list_reviews(product_id: int, db: Session = Depends(get_db)):
    items = db.query(models.Review).filter(models.Review.product_id == product_id).order_by(models.Review.created_at.desc()).all()
    return [{"id": x.id, "user_id": x.user_id, "user_name": x.user.name if x.user else None, "rating": x.rating, "title": x.title, "comment": x.comment, "created_at": x.created_at} for x in items]


@router.post("/products/{product_id}/reviews")
def upsert_review(product_id: int, payload: schemas.ReviewCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product: raise HTTPException(404, "Product not found")
    item = db.query(models.Review).filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        item.rating, item.title, item.comment = payload.rating, payload.title, payload.comment
    else:
        item = models.Review(user_id=current_user.id, product_id=product_id, **payload.model_dump()); db.add(item)
    db.flush()
    product.rating = float(db.query(func.avg(models.Review.rating)).filter(models.Review.product_id == product_id).scalar() or payload.rating)
    db.commit(); db.refresh(item)
    return {"id": item.id, "rating": item.rating, "product_rating": product.rating}


@router.post("/coupons")
def create_coupon(payload: schemas.CouponCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_role(["admin"]))):
    if db.query(models.Coupon).filter(func.lower(models.Coupon.code) == payload.code.lower()).first(): raise HTTPException(409, "Coupon already exists")
    item = models.Coupon(**payload.model_dump()); item.code = item.code.upper(); db.add(item); db.commit(); db.refresh(item); return item


@router.get("/coupons")
def list_coupons(db: Session = Depends(get_db), current_user: models.User = Depends(require_role(["admin"]))):
    return db.query(models.Coupon).order_by(models.Coupon.id.desc()).all()


@router.post("/coupons/validate")
def validate_coupon(code: str, amount: float, db: Session = Depends(get_db)):
    item = db.query(models.Coupon).filter(func.lower(models.Coupon.code) == code.lower()).first()
    if not item or not item.active or (item.expires_at and item.expires_at < datetime.utcnow()) or amount < item.minimum_amount: raise HTTPException(400, "Coupon is invalid or does not meet its requirements")
    discount = amount * item.discount_value / 100 if item.discount_type == "percent" else item.discount_value
    return {"code": item.code, "discount": round(min(discount, amount), 2), "total": round(max(0, amount-discount), 2)}
