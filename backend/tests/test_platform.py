import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app import models, schemas
from app.langchain_agent import _local_embedding, _similarity, route_specialists
from app.routes.catalog import search_catalog, add_wishlist, upsert_review
from app.routes.customer_intelligence import upsert_memory, recommendations


class PlatformTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        self.user = models.User(name="Buyer", email="buyer@test.dev", password="hash", role="buyer")
        vendor_user = models.User(name="Vendor", email="vendor@test.dev", password="hash", role="vendor")
        category = models.Category(name="Computers")
        self.db.add_all([self.user, vendor_user, category]); self.db.flush()
        vendor = models.Vendor(company_name="Tech", contact_email="vendor@test.dev", user_id=vendor_user.id)
        self.db.add(vendor); self.db.flush()
        products = [
            models.Product(name="Work Laptop", description="Portable office computer", sku="LAP-1", price=1200, vendor_id=vendor.id, category_id=category.id, brand="Acme", rating=4.8),
            models.Product(name="Laptop Dock", description="Compatible office accessory", sku="DOC-1", price=180, vendor_id=vendor.id, category_id=category.id, brand="Acme", rating=4.5),
        ]
        self.db.add_all(products); self.db.flush()
        self.db.add_all([models.Inventory(product_id=p.id, stock_quantity=10, reorder_level=2) for p in products])
        self.db.commit(); self.products = products

    def tearDown(self): self.db.close()

    def test_specialist_planner_routes_complex_request(self):
        plan = route_specialists("Build me a complete laptop setup under 2000 and check stock")
        self.assertTrue(plan["complex"])
        self.assertIn("pricing_agent", plan["specialists"])
        self.assertIn("inventory_agent", plan["specialists"])
        self.assertIn("recommendation_agent", plan["specialists"])

    def test_local_vector_similarity(self):
        question = _local_embedding("laptop warranty coverage")
        relevant = _local_embedding("laptop warranty lasts one year")
        unrelated = _local_embedding("fresh grocery delivery")
        self.assertGreater(_similarity(question, relevant), _similarity(question, unrelated))

    def test_search_wishlist_review_memory_and_recommendations(self):
        result = search_catalog(q="laptop", category_id=None, brand=None, min_price=None, max_price=1500, min_rating=4, in_stock=True, sort="relevance", limit=24, db=self.db)
        self.assertEqual(result["count"], 2)
        add_wishlist(schemas.WishlistCreate(product_id=self.products[1].id), self.db, self.user)
        review = upsert_review(self.products[0].id, schemas.ReviewCreate(rating=5, title="Great", comment="Reliable"), self.db, self.user)
        self.assertEqual(review["rating"], 5)
        upsert_memory(schemas.MemoryUpsert(key="brand", value="Acme"), self.db, self.user)
        items = recommendations(8, self.db, self.user)
        self.assertEqual(items[0]["product"]["id"], self.products[1].id)
        self.assertIn("preferred brand", items[0]["reason"])


if __name__ == "__main__":
    unittest.main()
