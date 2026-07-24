"""Neo4j projection and read-only retrieval for the commerce assistant."""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app import models

load_dotenv()

SOURCE = "b2b-ecommerce"


class Neo4jNotConfigured(RuntimeError):
    pass


def _settings() -> tuple[str, str, str, str]:
    uri = os.getenv("NEO4J_URI", "").strip()
    username = os.getenv("NEO4J_USERNAME", "neo4j").strip()
    password = os.getenv("NEO4J_PASSWORD", "")
    database = os.getenv("NEO4J_DATABASE", "neo4j").strip()
    if not uri or not password:
        raise Neo4jNotConfigured("NEO4J_URI and NEO4J_PASSWORD are required")
    return uri, username, password, database


def is_configured() -> bool:
    try:
        _settings()
        return True
    except Neo4jNotConfigured:
        return False


def _driver():
    # Some macOS/Python virtual environments do not expose a system CA path.
    # Aura requires TLS, so use certifi's maintained trust bundle when no
    # explicit certificate file has been configured by the deployment.
    if not os.getenv("SSL_CERT_FILE"):
        try:
            import certifi
            os.environ["SSL_CERT_FILE"] = certifi.where()
        except ImportError:
            pass

    try:
        from neo4j import GraphDatabase
    except ImportError as exc:
        raise Neo4jNotConfigured("Install the neo4j Python package") from exc

    uri, username, password, _ = _settings()
    return GraphDatabase.driver(uri, auth=(username, password))


def _value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _execute(driver, query: str, parameters: dict | None = None):
    _, _, _, database = _settings()
    records, _, _ = driver.execute_query(
        query,
        parameters_=parameters or {},
        database_=database,
        routing_="r",
    )
    return [dict(record) for record in records]


def _write(driver, query: str, rows: list[dict] | None = None):
    _, _, _, database = _settings()
    driver.execute_query(
        query,
        parameters_={"rows": rows or [], "source": SOURCE},
        database_=database,
        routing_="w",
    )


def verify_connectivity() -> dict:
    if not is_configured():
        return {"configured": False, "connected": False}
    try:
        with _driver() as driver:
            driver.verify_connectivity()
        return {"configured": True, "connected": True}
    except Exception as exc:
        return {"configured": True, "connected": False, "error": str(exc)}


def sync_graph(db: Session) -> dict[str, int]:
    """Replace only this application's graph projection with a fresh snapshot."""
    users = [
        {"id": u.id, "name": u.name, "email": u.email, "role": u.role}
        for u in db.query(models.User).all()
    ]
    vendors = [
        {
            "id": v.id,
            "company_name": v.company_name,
            "contact_email": v.contact_email,
            "phone": v.phone,
            "user_id": v.user_id,
        }
        for v in db.query(models.Vendor).all()
    ]
    products = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "sku": p.sku,
            "price": p.price,
            "vendor_id": p.vendor_id,
        }
        for p in db.query(models.Product).all()
    ]
    inventory = [
        {
            "id": i.id,
            "product_id": i.product_id,
            "stock_quantity": i.stock_quantity,
            "reorder_level": i.reorder_level,
        }
        for i in db.query(models.Inventory).all()
    ]
    orders = [
        {
            "id": o.id,
            "buyer_id": o.buyer_id,
            "status": o.status,
            "total_amount": o.total_amount,
            "created_at": _value(o.created_at),
            "delivered_at": _value(o.delivered_at),
        }
        for o in db.query(models.Order).all()
    ]
    order_items = [
        {
            "id": i.id,
            "order_id": i.order_id,
            "product_id": i.product_id,
            "vendor_id": i.vendor_id,
            "quantity": i.quantity,
            "unit_price": i.unit_price,
            "subtotal": i.subtotal,
        }
        for i in db.query(models.OrderItem).all()
    ]
    purchase_orders = [
        {
            "id": po.id,
            "vendor_id": po.vendor_id,
            "status": po.status,
            "total_amount": po.total_amount,
            "created_at": _value(po.created_at),
            "received_at": _value(po.received_at),
        }
        for po in db.query(models.PurchaseOrder).all()
    ]
    purchase_order_items = [
        {
            "id": i.id,
            "purchase_order_id": i.purchase_order_id,
            "product_id": i.product_id,
            "quantity": i.quantity,
            "unit_price": i.unit_price,
            "subtotal": i.subtotal,
        }
        for i in db.query(models.PurchaseOrderItem).all()
    ]

    constraints = (
        "CREATE CONSTRAINT b2b_user_id IF NOT EXISTS FOR (n:User) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT b2b_vendor_id IF NOT EXISTS FOR (n:Vendor) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT b2b_product_id IF NOT EXISTS FOR (n:Product) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT b2b_inventory_id IF NOT EXISTS FOR (n:Inventory) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT b2b_order_id IF NOT EXISTS FOR (n:Order) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT b2b_purchase_order_id IF NOT EXISTS FOR (n:PurchaseOrder) REQUIRE n.id IS UNIQUE",
    )

    with _driver() as driver:
        for constraint in constraints:
            _write(driver, constraint)
        _write(driver, "MATCH (n {source: $source}) DETACH DELETE n")
        _write(driver, "UNWIND $rows AS row CREATE (n:User) SET n = row, n.source = $source", users)
        _write(driver, "UNWIND $rows AS row CREATE (n:Vendor) SET n = row, n.source = $source", vendors)
        _write(driver, "UNWIND $rows AS row CREATE (n:Product) SET n = row, n.source = $source", products)
        _write(driver, "UNWIND $rows AS row CREATE (n:Inventory) SET n = row, n.source = $source", inventory)
        _write(driver, "UNWIND $rows AS row CREATE (n:Order) SET n = row, n.source = $source", orders)
        _write(driver, "UNWIND $rows AS row CREATE (n:PurchaseOrder) SET n = row, n.source = $source", purchase_orders)

        _write(driver, "UNWIND $rows AS row MATCH (u:User {id: row.user_id}), (v:Vendor {id: row.id}) CREATE (u)-[:OWNS]->(v)", vendors)
        _write(driver, "UNWIND $rows AS row MATCH (v:Vendor {id: row.vendor_id}), (p:Product {id: row.id}) CREATE (v)-[:SELLS]->(p)", products)
        _write(driver, "UNWIND $rows AS row MATCH (p:Product {id: row.product_id}), (i:Inventory {id: row.id}) CREATE (p)-[:HAS_INVENTORY]->(i)", inventory)
        _write(driver, "UNWIND $rows AS row MATCH (u:User {id: row.buyer_id}), (o:Order {id: row.id}) CREATE (u)-[:PLACED]->(o)", orders)
        _write(driver, "UNWIND $rows AS row MATCH (o:Order {id: row.order_id}), (p:Product {id: row.product_id}) CREATE (o)-[:CONTAINS {item_id: row.id, quantity: row.quantity, unit_price: row.unit_price, subtotal: row.subtotal}]->(p)", order_items)
        _write(driver, "UNWIND $rows AS row MATCH (po:PurchaseOrder {id: row.id}), (v:Vendor {id: row.vendor_id}) CREATE (po)-[:ORDERED_FROM]->(v)", purchase_orders)
        _write(driver, "UNWIND $rows AS row MATCH (po:PurchaseOrder {id: row.purchase_order_id}), (p:Product {id: row.product_id}) CREATE (po)-[:CONTAINS {item_id: row.id, quantity: row.quantity, unit_price: row.unit_price, subtotal: row.subtotal}]->(p)", purchase_order_items)

    return {
        "users": len(users),
        "vendors": len(vendors),
        "products": len(products),
        "inventory": len(inventory),
        "orders": len(orders),
        "order_items": len(order_items),
        "purchase_orders": len(purchase_orders),
        "purchase_order_items": len(purchase_order_items),
    }


def _scope_for_user(current_user: models.User | None) -> dict[str, Any]:
    if not current_user:
        return {"role": "anonymous", "user_id": None}
    return {"role": current_user.role, "user_id": current_user.id}


def retrieve_context(question: str, current_user: models.User | None = None) -> dict[str, list[dict]]:
    """Retrieve relevant facts with fixed, read-only Cypher templates."""
    q = question.lower()
    context: dict[str, list[dict]] = {}
    scope = _scope_for_user(current_user)
    id_match = re.search(
        r"\b(purchase order|user|buyer|customer|order|product|vendor|supplier)\s*(?:id|#)?\s*(\d+)\b",
        q,
    ) or re.search(r"\b(id|#)\s*(\d+)\b", q)
    entity_id = int(id_match.group(2)) if id_match else None
    entity_type = None
    if id_match and id_match.group(1) not in ("id", "#"):
        entity_type = id_match.group(1)
        entity_id = int(id_match.group(2))
        if entity_type in ("user", "buyer", "customer"):
            entity_type = "buyer"
        elif entity_type == "supplier":
            entity_type = "vendor"
        elif entity_type == "purchase order":
            entity_type = "purchase_order"

    queries = {
        "overview": """
            MATCH (u:User {source: $source})
            WHERE $role = 'admin'
               OR ($role IN ['buyer', 'vendor'] AND u.id = $user_id)
            WITH count(u) AS users
            OPTIONAL MATCH (v:Vendor {source: $source})
            WHERE $role = 'admin'
               OR ($role = 'vendor' AND v.user_id = $user_id)
            WITH users, count(v) AS vendors
            OPTIONAL MATCH (p:Product {source: $source})
            WHERE $role IN ['admin', 'buyer']
               OR ($role = 'vendor' AND EXISTS {
                    MATCH (:Vendor {id: p.vendor_id, source: $source, user_id: $user_id})
               })
            WITH users, vendors, count(p) AS products
            OPTIONAL MATCH (o:Order {source: $source})
            WHERE $role = 'admin'
               OR ($role = 'buyer' AND o.buyer_id = $user_id)
               OR ($role = 'vendor' AND EXISTS {
                    MATCH (o)-[:CONTAINS]->(:Product)<-[:SELLS]-(:Vendor {source: $source, user_id: $user_id})
               })
            RETURN users, vendors, products, count(o) AS orders,
                   coalesce(sum(o.total_amount), 0) AS order_revenue
        """,
        "inventory": """
            MATCH (v:Vendor {source: $source})-[:SELLS]->(p:Product {source: $source})-[:HAS_INVENTORY]->(i:Inventory {source: $source})
            WHERE ($entity_id IS NULL OR p.id = $entity_id)
              AND (
                $role IN ['admin', 'buyer']
                OR ($role = 'vendor' AND v.user_id = $user_id)
              )
            RETURN p.id AS product_id, p.name AS product, p.sku AS sku,
                   v.company_name AS vendor, i.stock_quantity AS stock,
                   i.reorder_level AS reorder_level,
                   i.stock_quantity <= i.reorder_level AS low_stock
            ORDER BY i.stock_quantity ASC LIMIT 50
        """,
        "products": """
            MATCH (v:Vendor {source: $source})-[:SELLS]->(p:Product {source: $source})
            OPTIONAL MATCH (p)-[:HAS_INVENTORY]->(i:Inventory)
            WHERE ($entity_id IS NULL OR p.id = $entity_id)
              AND (
                $role IN ['admin', 'buyer']
                OR ($role = 'vendor' AND v.user_id = $user_id)
              )
            RETURN p.id AS product_id, p.name AS product, p.sku AS sku,
                   p.description AS description, p.price AS price,
                   v.company_name AS vendor, i.stock_quantity AS stock
            ORDER BY p.name LIMIT 50
        """,
        "orders": """
            MATCH (u:User {source: $source})-[:PLACED]->(o:Order {source: $source})
            OPTIONAL MATCH (o)-[line:CONTAINS]->(p:Product)
            WHERE (
                $role = 'admin'
                OR ($role = 'buyer' AND u.id = $user_id)
                OR ($role = 'vendor' AND EXISTS {
                    MATCH (o)-[:CONTAINS]->(:Product)<-[:SELLS]-(:Vendor {source: $source, user_id: $user_id})
                })
              )
              AND (
                $entity_id IS NULL
                OR ($entity_type = 'order' AND o.id = $entity_id)
                OR ($entity_type = 'buyer' AND u.id = $entity_id)
                OR ($entity_type = 'vendor' AND EXISTS {
                    MATCH (o)-[:CONTAINS]->(:Product)<-[:SELLS]-(:Vendor {id: $entity_id, source: $source})
                })
                OR ($entity_type IS NULL AND (o.id = $entity_id OR u.id = $entity_id))
              )
            RETURN o.id AS order_id, u.id AS buyer_id, u.name AS buyer,
                   o.status AS status, o.total_amount AS total,
                   o.created_at AS created_at, o.delivered_at AS delivered_at,
                   collect({product: p.name, quantity: line.quantity, subtotal: line.subtotal}) AS items
            ORDER BY o.created_at DESC LIMIT 50
        """,
        "vendors": """
            MATCH (v:Vendor {source: $source})
            OPTIONAL MATCH (v)-[:SELLS]->(p:Product)<-[line:CONTAINS]-(o:Order)
            WHERE ($entity_id IS NULL OR v.id = $entity_id)
              AND (
                $role = 'admin'
                OR ($role = 'vendor' AND v.user_id = $user_id)
              )
            RETURN v.id AS vendor_id, v.company_name AS vendor,
                   count(DISTINCT p) AS products, count(DISTINCT o) AS orders,
                   coalesce(sum(line.subtotal), 0) AS revenue
            ORDER BY revenue DESC LIMIT 50
        """,
        "users": """
            MATCH (u:User {source: $source})
            OPTIONAL MATCH (u)-[:PLACED]->(o:Order)
            WHERE ($entity_id IS NULL OR u.id = $entity_id)
              AND ($role = 'admin' OR u.id = $user_id)
            RETURN u.id AS user_id, u.name AS name, u.email AS email,
                   u.role AS role, count(o) AS orders,
                   coalesce(sum(o.total_amount), 0) AS total_spent
            ORDER BY total_spent DESC LIMIT 50
        """,
        "purchase_orders": """
            MATCH (po:PurchaseOrder {source: $source})-[:ORDERED_FROM]->(v:Vendor {source: $source})
            OPTIONAL MATCH (po)-[line:CONTAINS]->(p:Product)
            WHERE ($entity_id IS NULL OR po.id = $entity_id OR v.id = $entity_id)
              AND (
                $role = 'admin'
                OR ($role = 'vendor' AND v.user_id = $user_id)
              )
            RETURN po.id AS purchase_order_id, v.company_name AS vendor,
                   po.status AS status, po.total_amount AS total,
                   po.created_at AS created_at, po.received_at AS received_at,
                   collect({product: p.name, quantity: line.quantity, subtotal: line.subtotal}) AS items
            ORDER BY po.created_at DESC LIMIT 50
        """,
    }

    selected = {"overview"}
    keyword_groups = {
        "inventory": ("stock", "inventory", "reorder", "available"),
        "products": ("product", "sku", "catalog", "price"),
        "orders": ("order", "fulfillment", "delivery", "delivered", "revenue"),
        "vendors": ("vendor", "supplier", "seller", "sales"),
        "users": ("user", "buyer", "customer", "spent"),
        "purchase_orders": ("purchase order", "procurement", "received"),
    }
    for name, keywords in keyword_groups.items():
        if any(keyword in q for keyword in keywords):
            selected.add(name)
    if selected == {"overview"}:
        selected.update(("products", "orders"))

    if scope["role"] == "buyer":
        selected -= {"vendors", "purchase_orders"}
    elif scope["role"] == "vendor":
        selected -= {"users"}
    elif scope["role"] != "admin":
        selected = set()

    params = {
        "source": SOURCE,
        "entity_id": entity_id,
        "entity_type": entity_type,
        **scope,
    }
    with _driver() as driver:
        for name in selected:
            context[name] = _execute(driver, queries[name], params)
    return context
