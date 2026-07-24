from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models
from app.auth import get_current_user, require_role

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/admin")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"]))
):
    total_users = db.query(models.User).count()

    total_vendors = db.query(models.Vendor).count()

    total_products = db.query(models.Product).count()

    total_orders = db.query(models.Order).count()

    total_revenue = (
        db.query(func.sum(models.Order.total_amount))
        .scalar()
    ) or 0

    pending_orders = (
        db.query(models.Order)
        .filter(models.Order.status == "PENDING")
        .count()
    )

    low_stock = (
        db.query(models.Inventory)
        .filter(
            models.Inventory.stock_quantity <=
            models.Inventory.reorder_level
        )
        .count()
    )

    return {
        "total_users": total_users,
        "total_vendors": total_vendors,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "pending_orders": pending_orders,
        "low_stock_alerts": low_stock
    }


@router.get("/buyer/{buyer_id}")
def buyer_dashboard(
    buyer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != "admin" and current_user.id != buyer_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="You can only view your own dashboard")

    orders = (
        db.query(models.Order)
        .filter(models.Order.buyer_id == buyer_id)
        .all()
    )

    total_spent = sum(order.total_amount for order in orders)

    return {
        "buyer_id": buyer_id,
        "total_orders": len(orders),
        "total_spent": total_spent,
        "orders": orders
    }


@router.get("/vendor/{vendor_id}")
def vendor_dashboard(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != "admin":
        if current_user.role != "vendor" or not current_user.vendor or current_user.vendor.id != vendor_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="You can only view your own dashboard")

    products = (
        db.query(models.Product)
        .filter(models.Product.vendor_id == vendor_id)
        .count()
    )

    total_sales = (
        db.query(func.sum(models.OrderItem.subtotal))
        .filter(models.OrderItem.vendor_id == vendor_id)
        .scalar()
    ) or 0

    total_orders = (
        db.query(models.OrderItem.order_id)
        .filter(models.OrderItem.vendor_id == vendor_id)
        .distinct()
        .count()
    )

    return {
        "vendor_id": vendor_id,
        "products": products,
        "total_orders": total_orders,
        "total_sales": total_sales
    }
