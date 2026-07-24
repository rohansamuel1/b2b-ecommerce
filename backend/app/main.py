from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, apply_compatibility_migrations
from app import models
from app.database import SessionLocal

from app.routes import (
    auth,
    users,
    vendors,
    products,
    inventory,
    orders,
    agent,
    dashboard,
    analytics,
    purchase_orders,
    invoices,
    catalog,
    customer_intelligence,
    integrations,
)

app = FastAPI(title="B2B Multi-Vendor Ecommerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5177",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

apply_compatibility_migrations()
Base.metadata.create_all(bind=engine)


def bootstrap_ai_reference_data():
    """Make existing demo databases immediately useful for search, RAG, and recommendations."""
    db = SessionLocal()
    try:
        defaults = {
            "Computers": "Laptops, workstations, and computing equipment",
            "Electronics": "Business electronics and connected devices",
            "Tools": "Industrial tools and equipment",
        }
        categories = {}
        for name, description in defaults.items():
            category = db.query(models.Category).filter(models.Category.name == name).first()
            if not category:
                category = models.Category(name=name, description=description); db.add(category); db.flush()
            categories[name] = category
        for product in db.query(models.Product).all():
            if not product.category_id:
                lowered = product.name.lower()
                category = categories["Computers"] if "macbook" in lowered or "laptop" in lowered else categories["Tools"] if "drill" in lowered else categories["Electronics"]
                product.category_id = category.id
            if not product.brand:
                lowered = product.name.lower()
                product.brand = "Apple" if "macbook" in lowered else "Samsung" if "samsung" in lowered else "Ray-Ban" if "rayban" in lowered else "B2B Select"
        if not db.query(models.ProductDocument).first():
            db.add_all([
                models.ProductDocument(title="Standard warranty and returns", document_type="policy", content="Products include a one-year limited warranty unless the product listing says otherwise. Returns may be requested within 30 days of delivery for unused items. Approved refunds are issued after inspection."),
                models.ProductDocument(title="Business order support FAQ", document_type="faq", content="Customers can track an order from My Orders. If an estimated delivery date passes, contact support with the order ID. Administrators can update shipment events and review return requests."),
            ])
        if not db.query(models.ExternalOffer).first():
            for product in db.query(models.Product).all():
                db.add_all([
                    models.ExternalOffer(product_id=product.id, marketplace="MarketHub Demo", external_title=product.name, price=round(product.price * 0.97, 2), rating=round(max(3.8, (product.rating or 4.2)-0.1),1), review_count=120+product.id*17, availability="In stock", source_url="https://example.com/demo-offer"),
                    models.ExternalOffer(product_id=product.id, marketplace="SupplySquare Demo", external_title=product.name, price=round(product.price * 1.04, 2), rating=round(min(5, (product.rating or 4.2)+0.1),1), review_count=80+product.id*23, availability="Ships in 2 days", source_url="https://example.com/demo-offer"),
                ])
        db.commit()
    finally:
        db.close()


bootstrap_ai_reference_data()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(vendors.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(agent.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(purchase_orders.router)
app.include_router(invoices.router)
app.include_router(catalog.router)
app.include_router(customer_intelligence.router)
app.include_router(integrations.router)


@app.get("/")
def root():
    return {"message": "B2B Ecommerce API is running"}
