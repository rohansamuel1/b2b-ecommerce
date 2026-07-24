from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app import models, schemas
from app.auth import get_current_user, require_role
from app.database import get_db
from app import cache

router = APIRouter(tags=["Customer Intelligence"])

@router.get("/memory")
def get_memory(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    key=f"user:{current_user.id}:memory"; cached=cache.get_json(key)
    if cached is not None: return cached
    items=db.query(models.UserMemory).filter(models.UserMemory.user_id == current_user.id).order_by(models.UserMemory.key).all()
    payload=[{"id":x.id,"key":x.key,"value":x.value,"source":x.source,"updated_at":x.updated_at} for x in items]; cache.set_json(key,payload); return payload

@router.put("/memory")
def upsert_memory(payload: schemas.MemoryUpsert, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.UserMemory).filter_by(user_id=current_user.id, key=payload.key.lower().strip()).first()
    if item: item.value = payload.value.strip(); item.updated_at = datetime.utcnow()
    else: item = models.UserMemory(user_id=current_user.id, key=payload.key.lower().strip(), value=payload.value.strip()); db.add(item)
    db.commit(); db.refresh(item); cache.delete(f"user:{current_user.id}:memory"); return item

@router.delete("/memory/{key}", status_code=204)
def delete_memory(key: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.UserMemory).filter_by(user_id=current_user.id, key=key.lower()).first()
    if item: db.delete(item); db.commit()
    cache.delete(f"user:{current_user.id}:memory")

@router.post("/knowledge/documents")
def add_document(payload: schemas.DocumentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_role(["admin"]))):
    if payload.product_id and not db.query(models.Product).filter_by(id=payload.product_id).first(): raise HTTPException(404, "Product not found")
    item = models.ProductDocument(**payload.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@router.get("/knowledge/documents")
def list_documents(product_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.ProductDocument)
    if product_id: query = query.filter(models.ProductDocument.product_id == product_id)
    return query.order_by(models.ProductDocument.created_at.desc()).all()

@router.get("/recommendations")
def recommendations(limit: int = Query(8, ge=1, le=30), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    purchased = {x.product_id for x in db.query(models.OrderItem).join(models.Order).filter(models.Order.buyer_id == current_user.id).all()}
    wishlisted = {x.product_id for x in db.query(models.WishlistItem).filter_by(user_id=current_user.id).all()}
    memories = {x.key: x.value.lower() for x in db.query(models.UserMemory).filter_by(user_id=current_user.id).all()}
    products = db.query(models.Product).all(); scored=[]
    bought_products = [p for p in products if p.id in purchased]
    for p in products:
        if p.id in purchased: continue
        score, reasons = (2 if p.id in wishlisted else 0), (["saved to your wishlist"] if p.id in wishlisted else [])
        if memories.get("brand") and p.brand and memories["brand"] in p.brand.lower(): score += 4; reasons.append("matches your preferred brand")
        if memories.get("budget"):
            try:
                if p.price <= float(memories["budget"]): score += 2; reasons.append("within your saved budget")
            except ValueError: pass
        if any(bp.category_id and bp.category_id == p.category_id for bp in bought_products): score += 3; reasons.append("related to a previous purchase")
        score += (p.rating or 0) / 5
        if p.stock_quantity > 0: score += 0.5
        if score > 0: scored.append((score,p,reasons or ["highly rated catalog match"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": round(s,2), "reason": "; ".join(r), "product": {"id":p.id,"name":p.name,"price":p.price,"brand":p.brand,"rating":p.rating,"stock_quantity":p.stock_quantity,"image_url":p.image_url}} for s,p,r in scored[:limit]]

@router.get("/orders/{order_id}/shipment")
def get_shipment(order_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    order = db.query(models.Order).filter_by(id=order_id).first()
    if not order: raise HTTPException(404,"Order not found")
    if current_user.role != "admin" and order.buyer_id != current_user.id: raise HTTPException(403,"Not allowed")
    shipment = db.query(models.Shipment).filter_by(order_id=order_id).first()
    return shipment or {"order_id":order_id,"status":"NOT_CREATED","last_event":"Awaiting fulfillment"}

@router.put("/orders/{order_id}/shipment")
def update_shipment(order_id: int, payload: schemas.ShipmentUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(require_role(["admin"]))):
    if not db.query(models.Order).filter_by(id=order_id).first(): raise HTTPException(404,"Order not found")
    item = db.query(models.Shipment).filter_by(order_id=order_id).first()
    data = payload.model_dump(exclude_none=True)
    if item:
        for k,v in data.items(): setattr(item,k,v)
        item.updated_at=datetime.utcnow()
    else:
        item=models.Shipment(order_id=order_id, estimated_delivery=payload.estimated_delivery or datetime.utcnow()+timedelta(days=5), **{k:v for k,v in data.items() if k!='estimated_delivery'}); db.add(item)
    db.commit(); db.refresh(item); return item

@router.post("/orders/{order_id}/returns")
def create_return(order_id: int, payload: schemas.ReturnCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    order=db.query(models.Order).filter_by(id=order_id).first()
    if not order: raise HTTPException(404,"Order not found")
    if current_user.role != "admin" and order.buyer_id != current_user.id: raise HTTPException(403,"Not allowed")
    item=models.ReturnRequest(order_id=order_id,user_id=current_user.id,reason=payload.reason); db.add(item); db.commit(); db.refresh(item); return item

@router.get("/returns")
def list_returns(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    q=db.query(models.ReturnRequest)
    if current_user.role != "admin": q=q.filter(models.ReturnRequest.user_id==current_user.id)
    return q.order_by(models.ReturnRequest.created_at.desc()).all()

@router.put("/returns/{return_id}")
def update_return(return_id:int,payload:schemas.ReturnUpdate,db:Session=Depends(get_db),current_user:models.User=Depends(require_role(["admin"]))):
    item=db.query(models.ReturnRequest).filter_by(id=return_id).first()
    if not item: raise HTTPException(404,"Return not found")
    item.status=payload.status; item.resolution=payload.resolution; item.updated_at=datetime.utcnow(); db.commit(); db.refresh(item); return item
