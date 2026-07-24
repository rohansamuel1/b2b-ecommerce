from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import require_role

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/", response_model=list[schemas.InventoryOut])
def get_inventory(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    return db.query(models.Inventory).all()


@router.get("/low-stock", response_model=list[schemas.InventoryOut])
def get_low_stock_items(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    return (
        db.query(models.Inventory)
        .filter(models.Inventory.stock_quantity <= models.Inventory.reorder_level)
        .all()
    )


@router.put("/{product_id}", response_model=schemas.InventoryOut)
def update_stock(
    product_id: int,
    stock_quantity: int,
    reorder_level: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    inventory = (
        db.query(models.Inventory)
        .filter(models.Inventory.product_id == product_id)
        .first()
    )

    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")

    inventory.stock_quantity = stock_quantity
    inventory.reorder_level = reorder_level

    db.commit()
    db.refresh(inventory)

    return inventory
