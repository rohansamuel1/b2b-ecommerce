from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserRoleUpdate(BaseModel):
    role: Literal["admin", "buyer", "vendor"]


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class VendorCreate(BaseModel):
    company_name: str
    contact_email: EmailStr
    phone: Optional[str] = None
    user_id: int


class VendorOut(BaseModel):
    id: int
    company_name: str
    contact_email: EmailStr
    phone: Optional[str]
    user_id: int

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sku: str
    price: float
    image_url: Optional[str] = None
    vendor_id: int
    stock_quantity: int = 0
    reorder_level: int = 10
    category_id: Optional[int] = None
    brand: Optional[str] = None
    attributes: dict = Field(default_factory=dict)


class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    sku: str
    price: float
    image_url: Optional[str] = None
    vendor_id: int
    stock_quantity: int = 0
    reorder_level: int = 0
    category_id: Optional[int] = None
    brand: Optional[str] = None
    rating: float = 0
    attributes_json: str = "{}"

    class Config:
        from_attributes = True


class InventoryOut(BaseModel):
    id: int
    product_id: int
    stock_quantity: int
    reorder_level: int

    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


class PaymentMethodCreate(BaseModel):
    provider: Literal["stripe"] = "stripe"
    cardholder_name: str
    card_number: str
    expiry: str
    cvc: str


class OrderCreate(BaseModel):
    buyer_id: int
    items: List[OrderItemCreate] = Field(min_length=1)
    payment_method: Optional[PaymentMethodCreate] = None
    coupon_code: Optional[str] = None


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    vendor_id: int
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True


class FulfillmentLogOut(BaseModel):
    id: int
    order_id: int
    status: str
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    buyer_id: int
    status: str
    total_amount: float
    created_at: datetime
    delivered_at: Optional[datetime]
    coupon_code: Optional[str] = None
    discount_amount: float = 0
    items: List[OrderItemOut] = []
    fulfillment_logs: List[FulfillmentLogOut] = []

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str
    note: Optional[str] = None


class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class PurchaseOrderCreate(BaseModel):
    vendor_id: int
    items: List[PurchaseOrderItemCreate]


class PurchaseOrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True


class PurchaseOrderOut(BaseModel):
    id: int
    vendor_id: int
    status: str
    total_amount: float
    created_at: datetime
    received_at: Optional[datetime]
    items: List[PurchaseOrderItemOut] = []

    class Config:
        from_attributes = True


class PurchaseOrderStatusUpdate(BaseModel):
    status: str


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryOut(CategoryCreate):
    id: int
    class Config:
        from_attributes = True


class WishlistCreate(BaseModel):
    product_id: int


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = None
    comment: Optional[str] = None


class CouponCreate(BaseModel):
    code: str
    discount_type: Literal["percent", "fixed"] = "percent"
    discount_value: float = Field(gt=0)
    minimum_amount: float = Field(default=0, ge=0)
    active: bool = True
    expires_at: Optional[datetime] = None


class MemoryUpsert(BaseModel):
    key: str = Field(min_length=1, max_length=80)
    value: str = Field(min_length=1, max_length=1000)


class DocumentCreate(BaseModel):
    product_id: Optional[int] = None
    title: str
    document_type: str = "manual"
    content: str = Field(min_length=20)
    source_url: Optional[str] = None


class ReturnCreate(BaseModel):
    reason: str = Field(min_length=5, max_length=2000)


class ReturnUpdate(BaseModel):
    status: str
    resolution: Optional[str] = None


class ShipmentUpdate(BaseModel):
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    status: str
    estimated_delivery: Optional[datetime] = None
    last_event: Optional[str] = None


class MCPToolCall(BaseModel):
    tool: Literal["search_marketplaces", "compare_prices", "queue_email", "read_product_document", "query_catalog"]
    arguments: dict = Field(default_factory=dict)
