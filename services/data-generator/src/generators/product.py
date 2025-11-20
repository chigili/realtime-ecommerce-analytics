"""Product data generator."""
from typing import Dict, List, Any, Optional
import random
from .base import BaseGenerator


class ProductGenerator(BaseGenerator):
    """Generate product catalog."""
    
    CATEGORIES = {
        "electronics": {
            "subcategories": ["laptops", "phones", "tablets", "accessories"],
            "brands": ["TechBrand", "ProComputers", "SmartDevices"],
            "price_range": (50, 3000)
        },
        "clothing": {
            "subcategories": ["mens", "womens", "kids"],
            "brands": ["FashionCo", "StyleWear", "TrendyClothes"],
            "price_range": (15, 300)
        },
        "home": {
            "subcategories": ["furniture", "decor", "kitchen"],
            "brands": ["HomeStyle", "ComfortLiving", "ModernHome"],
            "price_range": (20, 2000)
        },
        "sports": {
            "subcategories": ["fitness", "outdoor", "team_sports"],
            "brands": ["ActiveGear", "FitPro", "SportsMaster"],
            "price_range": (10, 500)
        },
    }
    
    def __init__(self, num_products: int = 1000, seed: Optional[int] = None):
        super().__init__(seed)
        self.num_products = num_products
        self._product_cache = {}
        self._generate_products()
    
    def _generate_products(self):
        """Pre-generate product catalog."""
        for i in range(self.num_products):
            category = random.choice(list(self.CATEGORIES.keys()))
            cat_info = self.CATEGORIES[category]
            
            subcategory = random.choice(cat_info["subcategories"])
            brand = random.choice(cat_info["brands"])
            
            product_id = f"prod_{i:04d}"
            product_name = f"{brand} {subcategory.title()} {self.fake.word().title()}"
            
            base_price = random.uniform(*cat_info["price_range"])
            
            self._product_cache[product_id] = {
                "product_id": product_id,
                "sku": f"{category[:3].upper()}-{i:04d}",
                "name": product_name,
                "brand": brand,
                "category": category,
                "subcategory": subcategory,
                "base_price": round(base_price, 2),
                "cost": round(base_price * 0.6, 2),
                "stock_quantity": random.randint(0, 500),
                "avg_rating": round(random.uniform(3.0, 5.0), 1),
                "review_count": random.randint(0, 500),
                "in_stock": random.random() > 0.05
            }
    
    def get_random_product(self) -> Dict[str, Any]:
        """Get a random product."""
        product_id = random.choice(list(self._product_cache.keys()))
        return self._product_cache[product_id]
    
    def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get products in a category."""
        return [
            p for p in self._product_cache.values()
            if p["category"] == category
        ]
    
    def generate(self) -> Dict[str, Any]:
        """Generate a product (for ABC compliance)."""
        return self.get_random_product()
