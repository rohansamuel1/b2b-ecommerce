from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app import models, schemas
from app.auth import require_role

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=schemas.ProductOut)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    product_data = product.model_dump()

    stock_quantity = product_data.pop("stock_quantity")
    reorder_level = product_data.pop("reorder_level")
    attributes = product_data.pop("attributes", {})
    product_data["attributes_json"] = json.dumps(attributes)

    if product_data.get("category_id") and not db.query(models.Category).filter(models.Category.id == product_data["category_id"]).first():
        raise HTTPException(status_code=404, detail="Category not found")

    new_product = models.Product(**product_data)

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    inventory = models.Inventory(
        product_id=new_product.id,
        stock_quantity=stock_quantity,
        reorder_level=reorder_level
    )

    db.add(inventory)
    db.commit()

    return new_product


@router.get("/", response_model=list[schemas.ProductOut])
def get_products(
    search: str = "",
    category_id: int | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(models.Product.name.ilike(term) | models.Product.sku.ilike(term) | models.Product.description.ilike(term))
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    return query.all()


@router.get("/{product_id}", response_model=schemas.ProductOut)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    return db.query(models.Product).filter(models.Product.id == product_id).first()
