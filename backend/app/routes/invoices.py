from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.auth import get_current_user

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("/order/{order_id}")
def get_order_invoice(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    order = db.query(models.Order).filter(
        models.Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role != "admin" and order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own invoices")

    invoice_items = []

    for item in order.items:
        invoice_items.append({
            "product_id": item.product_id,
            "product_name": item.product.name if item.product else "Unknown",
            "vendor_id": item.vendor_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "subtotal": item.subtotal
        })

    return {
        "invoice_number": f"INV-{order.id:05d}",
        "order_id": order.id,
        "buyer_id": order.buyer_id,
        "status": order.status,
        "created_at": order.created_at,
        "delivered_at": order.delivered_at,
        "total_amount": order.total_amount,
        "items": invoice_items
    }
