from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models, schemas
from app.auth import require_role

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.post("/", response_model=schemas.VendorOut)
def create_vendor(
    vendor: schemas.VendorCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    new_vendor = models.Vendor(**vendor.model_dump())

    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)

    return new_vendor


@router.get("/", response_model=list[schemas.VendorOut])
def get_vendors(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    return db.query(models.Vendor).all()


@router.get("/{vendor_id}", response_model=schemas.VendorOut)
def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return vendor


@router.get("/{vendor_id}/products")
def get_vendor_products(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    return db.query(models.Product).filter(models.Product.vendor_id == vendor_id).all()


@router.get("/{vendor_id}/orders")
def get_vendor_orders(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    orders = (
        db.query(models.Order)
        .join(models.OrderItem)
        .filter(models.OrderItem.vendor_id == vendor_id)
        .distinct()
        .all()
    )

    return orders


@router.get("/{vendor_id}/sales-summary")
def get_vendor_sales_summary(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    total_sales = (
        db.query(func.sum(models.OrderItem.subtotal))
        .filter(models.OrderItem.vendor_id == vendor_id)
        .scalar()
    )

    total_units_sold = (
        db.query(func.sum(models.OrderItem.quantity))
        .filter(models.OrderItem.vendor_id == vendor_id)
        .scalar()
    )

    total_orders = (
        db.query(models.OrderItem.order_id)
        .filter(models.OrderItem.vendor_id == vendor_id)
        .distinct()
        .count()
    )

    return {
        "vendor_id": vendor_id,
        "total_sales": total_sales or 0,
        "total_units_sold": total_units_sold or 0,
        "total_orders": total_orders
    }


@router.get("/{vendor_id}/low-stock")
def get_vendor_low_stock(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    low_stock_items = (
        db.query(models.Inventory)
        .join(models.Product)
        .filter(models.Product.vendor_id == vendor_id)
        .filter(models.Inventory.stock_quantity <= models.Inventory.reorder_level)
        .all()
    )

    return low_stock_items
