from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="buyer")

    vendor = relationship("Vendor", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="buyer")
    wishlist_items = relationship("WishlistItem", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("UserMemory", back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    parent = relationship("Category", remote_side=[id])
    products = relationship("Product", back_populates="category")


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    contact_email = Column(String, nullable=False)
    phone = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="vendor")
    products = relationship("Product", back_populates="vendor")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    sku = Column(String, unique=True, index=True)
    price = Column(Float, nullable=False)
    image_url = Column(String)
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    brand = Column(String, index=True)
    rating = Column(Float, default=0)
    attributes_json = Column(Text, default="{}")

    vendor = relationship("Vendor", back_populates="products")
    category = relationship("Category", back_populates="products")
    inventory = relationship(
        "Inventory",
        back_populates="product",
        uselist=False
    )
    order_items = relationship(
        "OrderItem",
        back_populates="product"
    )
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    documents = relationship("ProductDocument", back_populates="product", cascade="all, delete-orphan")

    @property
    def stock_quantity(self):
        return self.inventory.stock_quantity if self.inventory else 0

    @property
    def reorder_level(self):
        return self.inventory.reorder_level if self.inventory else 0


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    stock_quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)

    product = relationship("Product", back_populates="inventory")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="PENDING")
    total_amount = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    coupon_code = Column(String, nullable=True)
    discount_amount = Column(Float, default=0)

    buyer = relationship("User", back_populates="orders")

    items = relationship(
        "OrderItem",
        back_populates="order"
    )

    fulfillment_logs = relationship(
        "FulfillmentLog",
        back_populates="order"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    vendor_id = Column(Integer, ForeignKey("vendors.id"))

    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    vendor = relationship("Vendor")


class FulfillmentLog(Base):
    __tablename__ = "fulfillment_logs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))

    status = Column(String, nullable=False)
    note = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    order = relationship(
        "Order",
        back_populates="fulfillment_logs"
    )


class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="wishlist_items")
    product = relationship("Product")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_review_user_product"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    title = Column(String)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")
    product = relationship("Product", back_populates="reviews")


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, index=True, nullable=False)
    discount_type = Column(String, default="percent")
    discount_value = Column(Float, nullable=False)
    minimum_amount = Column(Float, default=0)
    active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    carrier = Column(String, default="Demo Logistics")
    tracking_number = Column(String, unique=True, index=True)
    status = Column(String, default="PROCESSING")
    estimated_delivery = Column(DateTime, nullable=True)
    last_event = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    order = relationship("Order")


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String, default="REQUESTED")
    resolution = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    order = relationship("Order")
    user = relationship("User")


class UserMemory(Base):
    __tablename__ = "user_memories"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_user_memory_key"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    source = Column(String, default="explicit")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="memories")


class ProductDocument(Base):
    __tablename__ = "product_documents"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    title = Column(String, nullable=False)
    document_type = Column(String, default="manual")
    content = Column(Text, nullable=False)
    source_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", back_populates="documents")


class ExternalOffer(Base):
    __tablename__ = "external_offers"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    marketplace = Column(String, nullable=False)
    external_title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    rating = Column(Float, default=0)
    review_count = Column(Integer, default=0)
    availability = Column(String, default="In stock")
    source_url = Column(String)
    captured_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product")


class EmailOutbox(Base):
    __tablename__ = "email_outbox"

    id = Column(Integer, primary_key=True)
    recipient = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String, default="DEMO_QUEUED")
    related_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==========================
# PURCHASE ORDERS (B2B)
# ==========================

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)

    vendor_id = Column(
        Integer,
        ForeignKey("vendors.id")
    )

    status = Column(
        String,
        default="DRAFT"
    )

    total_amount = Column(
        Float,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    received_at = Column(
        DateTime,
        nullable=True
    )

    vendor = relationship("Vendor")

    items = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order"
    )


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)

    purchase_order_id = Column(
        Integer,
        ForeignKey("purchase_orders.id")
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id")
    )

    quantity = Column(
        Integer,
        nullable=False
    )

    unit_price = Column(
        Float,
        nullable=False
    )

    subtotal = Column(
        Float,
        nullable=False
    )

    purchase_order = relationship(
        "PurchaseOrder",
        back_populates="items"
    )

    product = relationship("Product")
