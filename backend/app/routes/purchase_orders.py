from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app import models, schemas
from app.auth import require_role

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.post("/", response_model=schemas.PurchaseOrderOut)
def create_purchase_order(
    purchase_order: schemas.PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    vendor = db.query(models.Vendor).filter(
        models.Vendor.id == purchase_order.vendor_id
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    new_po = models.PurchaseOrder(
        vendor_id=purchase_order.vendor_id,
        status="DRAFT",
        total_amount=0
    )

    db.add(new_po)
    db.commit()
    db.refresh(new_po)

    total_amount = 0

    for item in purchase_order.items:
        product = db.query(models.Product).filter(
            models.Product.id == item.product_id,
            models.Product.vendor_id == purchase_order.vendor_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found for this vendor"
            )

        subtotal = product.price * item.quantity
        total_amount += subtotal

        po_item = models.PurchaseOrderItem(
            purchase_order_id=new_po.id,
            product_id=product.id,
            quantity=item.quantity,
            unit_price=product.price,
            subtotal=subtotal
        )

        db.add(po_item)

    new_po.total_amount = total_amount

    db.commit()
    db.refresh(new_po)

    return new_po


@router.get("/", response_model=list[schemas.PurchaseOrderOut])
def get_purchase_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    return db.query(models.PurchaseOrder).all()


@router.get("/{purchase_order_id}", response_model=schemas.PurchaseOrderOut)
def get_purchase_order(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    purchase_order = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.id == purchase_order_id
    ).first()

    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    return purchase_order


@router.get("/vendor/{vendor_id}", response_model=list[schemas.PurchaseOrderOut])
def get_purchase_orders_by_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    return db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.vendor_id == vendor_id
    ).all()


@router.put("/{purchase_order_id}/status", response_model=schemas.PurchaseOrderOut)
def update_purchase_order_status(
    purchase_order_id: int,
    status_update: schemas.PurchaseOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    purchase_order = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.id == purchase_order_id
    ).first()

    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    purchase_order.status = status_update.status

    if status_update.status.upper() == "RECEIVED":
        purchase_order.received_at = datetime.utcnow()

        for item in purchase_order.items:
            inventory = db.query(models.Inventory).filter(
                models.Inventory.product_id == item.product_id
            ).first()

            if inventory:
                inventory.stock_quantity += item.quantity
            else:
                inventory = models.Inventory(
                    product_id=item.product_id,
                    stock_quantity=item.quantity,
                    reorder_level=10
                )
                db.add(inventory)

    db.commit()
    db.refresh(purchase_order)

    return purchase_order
