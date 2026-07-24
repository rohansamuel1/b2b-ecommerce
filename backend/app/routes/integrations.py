"""Local MCP-compatible demo gateway plus optional live-provider registry."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/integrations", tags=["Integrations"])

TOOL_CATALOG = [
    {"name":"search_marketplaces","description":"Search reproducible demo marketplace offers and review summaries","mode":"demo"},
    {"name":"compare_prices","description":"Compare marketplace prices for a catalog product","mode":"demo"},
    {"name":"queue_email","description":"Queue a support or order email in the local demo outbox","mode":"demo"},
    {"name":"read_product_document","description":"Read an indexed product manual, FAQ, warranty, or policy","mode":"local"},
    {"name":"query_catalog","description":"Read the application catalog through a constrained tool","mode":"local"},
]


@router.get("/mcp")
def mcp_registry(current_user: models.User = Depends(require_role(["admin"]))):
    return {"protocol":"MCP-compatible local gateway","mode":"demo","tools":TOOL_CATALOG,"live_providers":[],"note":"Every listed tool executes locally. External marketplace and email results are clearly marked demo data."}


def _offers(db: Session, product_id: int):
    product = db.query(models.Product).filter_by(id=product_id).first()
    if not product: raise HTTPException(404,"Product not found")
    offers = db.query(models.ExternalOffer).filter_by(product_id=product_id).all()
    return product, offers


@router.get("/marketplaces/{product_id}")
def compare_marketplaces(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    product, offers = _offers(db, product_id)
    rows=[{"marketplace":"B2B Commerce","title":product.name,"price":product.price,"rating":product.rating,"review_count":len(product.reviews),"availability":f"{product.stock_quantity} in stock","source":"live local catalog","demo":False}]
    rows += [{"marketplace":x.marketplace,"title":x.external_title,"price":x.price,"rating":x.rating,"review_count":x.review_count,"availability":x.availability,"source_url":x.source_url,"source":"seeded external snapshot","demo":True} for x in offers]
    best=min(rows,key=lambda x:x["price"])
    return {"product_id":product_id,"product":product.name,"offers":rows,"best_price":{"marketplace":best["marketplace"],"price":best["price"]},"disclaimer":"External offers and reviews are deterministic demo snapshots, not live marketplace data."}


@router.get("/outbox")
def outbox(db:Session=Depends(get_db),current_user:models.User=Depends(require_role(["admin"]))):
    return db.query(models.EmailOutbox).order_by(models.EmailOutbox.created_at.desc()).all()


@router.post("/mcp/call")
def call_tool(payload:schemas.MCPToolCall,db:Session=Depends(get_db),current_user:models.User=Depends(get_current_user)):
    args=payload.arguments
    if payload.tool in {"search_marketplaces","compare_prices"}:
        product_id=int(args.get("product_id",0)); return {"tool":payload.tool,"result":compare_marketplaces(product_id,db,current_user)}
    if payload.tool=="queue_email":
        recipient=str(args.get("recipient") or current_user.email); subject=str(args.get("subject") or "B2B Commerce update"); body=str(args.get("body") or "Your requested commerce update is ready.")
        item=models.EmailOutbox(recipient=recipient,subject=subject,body=body,related_order_id=args.get("order_id")); db.add(item); db.commit(); db.refresh(item)
        return {"tool":payload.tool,"result":{"queued":True,"outbox_id":item.id,"status":item.status,"demo":True}}
    if payload.tool=="read_product_document":
        doc=db.query(models.ProductDocument).filter_by(id=int(args.get("document_id",0))).first()
        if not doc: raise HTTPException(404,"Document not found")
        return {"tool":payload.tool,"result":{"id":doc.id,"title":doc.title,"content":doc.content,"type":doc.document_type}}
    if payload.tool=="query_catalog":
        query=str(args.get("query","")).strip(); rows=db.query(models.Product)
        if query: rows=rows.filter(models.Product.name.ilike(f"%{query}%"))
        return {"tool":payload.tool,"result":[{"id":p.id,"name":p.name,"price":p.price,"stock":p.stock_quantity,"rating":p.rating} for p in rows.limit(20).all()]}
    raise HTTPException(400,"Unsupported tool")
