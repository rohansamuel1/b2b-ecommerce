from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models
from app.auth import require_role

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/intelligence")
def business_intelligence(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    category_revenue = (
        db.query(models.Category.name, func.coalesce(func.sum(models.OrderItem.subtotal), 0))
        .join(models.Product, models.Product.category_id == models.Category.id)
        .join(models.OrderItem, models.OrderItem.product_id == models.Product.id)
        .group_by(models.Category.name).all()
    )
    top_products = (
        db.query(models.Product.id, models.Product.name, func.coalesce(func.sum(models.OrderItem.subtotal), 0).label("revenue"), func.coalesce(func.sum(models.OrderItem.quantity), 0).label("units"))
        .join(models.OrderItem).group_by(models.Product.id)
        .order_by(func.sum(models.OrderItem.subtotal).desc()).limit(10).all()
    )
    order_statuses = db.query(models.Order.status, func.count(models.Order.id)).group_by(models.Order.status).all()
    returns = db.query(models.ReturnRequest.status, func.count(models.ReturnRequest.id)).group_by(models.ReturnRequest.status).all()
    return {
        "category_revenue": [{"category": name, "revenue": float(revenue)} for name, revenue in category_revenue],
        "top_products": [{"product_id": pid, "product": name, "revenue": float(revenue), "units": int(units)} for pid, name, revenue, units in top_products],
        "order_statuses": [{"status": status, "count": count} for status, count in order_statuses],
        "returns": [{"status": status, "count": count} for status, count in returns],
    }


@router.get("/vendors")
def vendor_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    vendors = db.query(models.Vendor).all()

    result = []

    for vendor in vendors:
        revenue = (
            db.query(func.sum(models.OrderItem.subtotal))
            .filter(models.OrderItem.vendor_id == vendor.id)
            .scalar()
        ) or 0

        orders = (
            db.query(models.OrderItem.order_id)
            .filter(models.OrderItem.vendor_id == vendor.id)
            .distinct()
            .count()
        )

        result.append({
            "vendor_id": vendor.id,
            "company_name": vendor.company_name,
            "revenue": revenue,
            "orders": orders
        })

    return result
