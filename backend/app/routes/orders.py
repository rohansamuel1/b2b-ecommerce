from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from uuid import uuid4

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, require_role

router = APIRouter(prefix="/orders", tags=["Orders"])


def create_mock_stripe_payment(payment_method: schemas.PaymentMethodCreate | None, amount: float):
    if not payment_method:
        return None

    card_number = payment_method.card_number.replace(" ", "")
    if len(card_number) < 12 or not card_number.isdigit():
        raise HTTPException(status_code=400, detail="Enter a valid dummy Stripe card number")

    if len(payment_method.cvc) < 3 or not payment_method.cvc.isdigit():
        raise HTTPException(status_code=400, detail="Enter a valid dummy Stripe CVC")

    if "/" not in payment_method.expiry:
        raise HTTPException(status_code=400, detail="Enter a dummy Stripe expiry as MM/YY")

    return {
        "id": f"pi_mock_{uuid4().hex[:16]}",
        "amount": amount,
        "currency": "usd",
        "status": "succeeded",
        "last4": card_number[-4:],
    }


@router.post("/", response_model=schemas.OrderOut)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ("admin", "buyer"):
        raise HTTPException(status_code=403, detail="Only buyers can place orders")

    if current_user.role != "admin" and order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only create orders for yourself")

    requested_quantities = {}
    for item in order.items:
        requested_quantities[item.product_id] = (
            requested_quantities.get(item.product_id, 0) + item.quantity
        )

    validated_items = []
    total_amount = 0
    for product_id, quantity in requested_quantities.items():
        product = db.query(models.Product).filter(models.Product.id == product_id).first()

        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        inventory = db.query(models.Inventory).filter(
            models.Inventory.product_id == product_id
        ).first()

        if not inventory:
            raise HTTPException(status_code=400, detail=f"{product.name} is not available")

        if inventory.stock_quantity < quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Only {inventory.stock_quantity} units of {product.name} are available"
            )

        subtotal = product.price * quantity
        total_amount += subtotal
        validated_items.append((product, inventory, quantity, subtotal))

    discount_amount = 0
    coupon = None
    if order.coupon_code:
        coupon = db.query(models.Coupon).filter(func.lower(models.Coupon.code) == order.coupon_code.lower()).first()
        if not coupon or not coupon.active or (coupon.expires_at and coupon.expires_at < datetime.utcnow()) or total_amount < coupon.minimum_amount:
            raise HTTPException(status_code=400, detail="Coupon is invalid or does not meet its requirements")
        discount_amount = total_amount * coupon.discount_value / 100 if coupon.discount_type == "percent" else coupon.discount_value
        discount_amount = round(min(discount_amount, total_amount), 2)
        total_amount = round(total_amount - discount_amount, 2)

    payment = create_mock_stripe_payment(order.payment_method, total_amount)

    try:
        new_order = models.Order(
            buyer_id=order.buyer_id,
            status="PENDING",
            total_amount=total_amount,
            coupon_code=coupon.code if coupon else None,
            discount_amount=discount_amount,
        )
        db.add(new_order)
        db.flush()

        for product, inventory, quantity, subtotal in validated_items:
            db.add(models.OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                vendor_id=product.vendor_id,
                quantity=quantity,
                unit_price=product.price,
                subtotal=subtotal
            ))
            inventory.stock_quantity -= quantity

        db.add(models.FulfillmentLog(
            order_id=new_order.id,
            status="PENDING",
            note=(
                f"Order created. Dummy Stripe payment {payment['id']} approved "
                f"for ${payment['amount']:.2f} ending in {payment['last4']}."
                if payment else "Order created"
            )
        ))
        db.add(models.Shipment(
            order_id=new_order.id,
            tracking_number=f"DEMO-{new_order.id:06d}",
            status="PROCESSING",
            estimated_delivery=datetime.utcnow() + timedelta(days=5),
            last_event="Order confirmed and awaiting carrier pickup",
        ))

        db.commit()
        db.refresh(new_order)
    except Exception:
        db.rollback()
        raise

    return new_order


@router.get("/", response_model=list[schemas.OrderOut])
def get_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Order)
    if current_user.role != "admin":
        query = query.filter(models.Order.buyer_id == current_user.id)
    return query.all()


@router.get("/user/{user_id}", response_model=list[schemas.OrderOut])
def get_orders_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only view your own orders")
    return db.query(models.Order).filter(models.Order.buyer_id == user_id).all()


@router.get("/{order_id}", response_model=schemas.OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role != "admin" and order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own orders")

    return order


@router.put("/{order_id}/status", response_model=schemas.OrderOut)
def update_order_status(
    order_id: int,
    status_update: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = status_update.status

    if status_update.status.upper() == "DELIVERED":
        order.delivered_at = datetime.utcnow()

    log = models.FulfillmentLog(
        order_id=order.id,
        status=status_update.status,
        note=status_update.note
    )

    db.add(log)
    db.commit()
    db.refresh(order)

    return order


@router.get("/{order_id}/fulfillment-duration")
def get_fulfillment_duration(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role != "admin" and order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own orders")

    if not order.delivered_at:
        return {
            "order_id": order.id,
            "status": order.status,
            "message": "Order has not been delivered yet"
        }

    duration = order.delivered_at - order.created_at

    return {
        "order_id": order.id,
        "status": order.status,
        "created_at": order.created_at,
        "delivered_at": order.delivered_at,
        "fulfillment_duration_days": duration.days,
        "fulfillment_duration_seconds": duration.total_seconds()
    }
