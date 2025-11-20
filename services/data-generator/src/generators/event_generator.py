"""Event generation with realistic behavioral patterns - FIXED VERSION."""

import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .session import UserSession


class EventGenerator:
    """Generates realistic events based on user sessions and patterns."""

    def __init__(self, user_generator, product_generator):
        """Initialize event generator."""
        self.user_generator = user_generator
        self.product_generator = product_generator

    def generate_device_info(self) -> Dict:
        """Generate realistic device information."""
        device_types = ["desktop", "mobile", "tablet"]
        device_type = random.choice(device_types)

        os_map = {
            "desktop": ["Windows", "macOS", "Linux"],
            "mobile": ["iOS", "Android"],
            "tablet": ["iOS", "Android"],
        }

        return {
            "type": device_type,
            "os": random.choice(os_map[device_type]),
            "browser": random.choice(["Chrome", "Safari", "Firefox", "Edge"]),
        }

    def generate_geo_info(self) -> Dict:
        """Generate realistic geographic information."""
        locations = [
            {"country": "US", "city": "New York", "lat": 40.7128, "lon": -74.0060},
            {"country": "US", "city": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
            {"country": "UK", "city": "London", "lat": 51.5074, "lon": -0.1278},
            {"country": "CA", "city": "Toronto", "lat": 43.6532, "lon": -79.3832},
        ]
        loc = random.choice(locations)
        return {
            "country": loc["country"],
            "city": loc["city"],
            "timezone": "UTC",
            "lat": loc["lat"],
            "lon": loc["lon"],
        }

    def generate_next_event(self, session: UserSession) -> Dict[str, Any]:
        """
        Generate the next realistic event for a session.
        Abandonment is now handled by session.is_expired() only.
        """
        # Update session
        session.last_event_time = datetime.now(timezone.utc)
        session.events_generated += 1

        # First event is always session start
        if session.events_generated == 1:
            return self._generate_session_start(session)

        # Check if session should end naturally (via is_expired logic)
        if session.is_expired():
            return self._generate_session_end(session)

        # STATE MACHINE ROUTER
        if session.state == "browsing":
            return self._generate_browsing_event(session)
        elif session.state == "shopping":
            return self._generate_shopping_event(session)
        elif session.state == "checkout":
            return self._generate_checkout_event(session)
        else:
            return self._generate_browsing_event(session)

    def _generate_session_start(self, session: UserSession) -> Dict[str, Any]:
        """Generate session start event."""
        user = self.user_generator.get_user(session.user_id)

        return {
            "event_type": "session_start",
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "timestamp": session.start_time.isoformat(),
            "session_id": session.session_id,
            "user_id": session.user_id,
            "user_segment": session.user_segment,
            "session_state": session.state,
            "will_purchase": session.will_purchase,
            "device": self.generate_device_info(),
            "geo": self.generate_geo_info(),
        }

    def _generate_browsing_event(self, session: UserSession) -> Dict[str, Any]:
        """
        Generate events while user is browsing.
        Let natural session expiry handle abandonment.
        """
        # Weighted choice of what browsing users do
        action = random.choices(
            ["page_view", "search", "product_view"], weights=[0.40, 0.20, 0.40]
        )[0]

        if action == "product_view":
            # Transition to shopping
            session.state = "shopping"
            return self._generate_product_view(session)
        elif action == "search":
            return self._generate_search(session)
        else:
            session.pages_viewed += 1
            return self._generate_page_view(session)

    def _generate_shopping_event(self, session: UserSession) -> Dict[str, Any]:
        """
        Generate events while user is shopping.
        Let natural session expiry handle abandonment.
        """
        # After viewing 2-3 products, decide: add to cart or keep browsing
        if len(session.viewed_products) >= 2 and len(session.cart) == 0:
            # 40% of product viewers add to cart
            if random.random() < 0.40:
                return self._generate_add_to_cart(session)

        # If cart has items, 60% move to checkout
        if len(session.cart) > 0 and random.random() < 0.60:
            session.state = "checkout"
            return self._generate_cart_view(session)

        # Continue viewing products
        return self._generate_product_view(session)

    def _generate_checkout_event(self, session: UserSession) -> Dict[str, Any]:
        """
        Generate checkout events.
        Users who intended to purchase have high completion rate.
        """
        # Even users who "will_purchase" might abandon (price shock, etc.)
        if session.will_purchase:
            # 85% complete if they intended to purchase
            if random.random() < 0.85:
                session.state = "completed"
                return self._generate_purchase(session)

        # Abandon cart
        session.state = "abandoned"
        return self._generate_session_end(session)

    def _generate_page_view(self, session: UserSession) -> Dict[str, Any]:
        """Generate page view event."""
        page_types = ["home", "category", "search_results", "about"]
        page_type = random.choice(page_types)

        return {
            "event_type": "page_view",
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session.session_id,
            "user_id": session.user_id,
            "session_state": session.state,
            "page_type": page_type,
            "pages_in_session": session.pages_viewed,
            "device": self.generate_device_info(),
            "geo": self.generate_geo_info(),
        }

    def _generate_search(self, session: UserSession) -> Dict[str, Any]:
        """Generate search event."""
        search_queries = [
            "laptop",
            "wireless headphones",
            "running shoes",
            "coffee maker",
            "yoga mat",
            "desk chair",
            "winter jacket",
            "smartphone",
        ]
        query = random.choice(search_queries)
        session.searches.append(query)

        return {
            "event_type": "search",
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session.session_id,
            "user_id": session.user_id,
            "session_state": session.state,
            "search_query": query,
            "results_count": random.randint(10, 200),
            "device": self.generate_device_info(),
            "geo": self.generate_geo_info(),
        }

    def _generate_product_view(self, session: UserSession) -> Dict[str, Any]:
        """Generate product view event."""
        product = self.product_generator.get_random_product()

        # Don't view same product twice in a row
        if (
            session.viewed_products
            and session.viewed_products[-1] == product["product_id"]
        ):
            product = self.product_generator.get_random_product()

        session.viewed_products.append(product["product_id"])

        return {
            "event_type": "product_viewed",
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session.session_id,
            "user_id": session.user_id,
            "session_state": session.state,
            "product_id": product["product_id"],
            "product_name": product["name"],
            "product_category": product["category"],
            "price": product["base_price"],
            "in_stock": product["in_stock"],
            "products_viewed_in_session": len(session.viewed_products),
            "device": self.generate_device_info(),
            "geo": self.generate_geo_info(),
        }

    def _generate_add_to_cart(self, session: UserSession) -> Dict[str, Any]:
        """Generate add to cart event."""
        if not session.viewed_products:
            return self._generate_product_view(session)

        # Get last viewed product
        product_id = session.viewed_products[-1]
        product = self.product_generator._product_cache.get(product_id)

        if not product:
            return self._generate_product_view(session)

        # Add to cart
        session.cart.append(product)

        return {
            "event_type": "add_to_cart",
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session.session_id,
            "user_id": session.user_id,
            "session_state": session.state,
            "product_id": product["product_id"],
            "product_name": product["name"],
            "price": product["base_price"],
            "quantity": 1,
            "cart_total": session.get_cart_value(),
            "cart_item_count": len(session.cart),
            "device": self.generate_device_info(),
            "geo": self.generate_geo_info(),
        }

    def _generate_cart_view(self, session: UserSession) -> Dict[str, Any]:
        """Generate cart view event (transition to checkout)."""
        return {
            "event_type": "cart_viewed",
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session.session_id,
            "user_id": session.user_id,
            "session_state": session.state,
            "cart_total": session.get_cart_value(),
            "cart_item_count": len(session.cart),
            "device": self.generate_device_info(),
            "geo": self.generate_geo_info(),
        }

    def _generate_purchase(self, session: UserSession) -> Dict[str, Any]:
        """Generate purchase event."""
        if not session.cart:
            session.state = "abandoned"
            return self._generate_session_end(session)

        subtotal = session.get_cart_value()
        tax = subtotal * 0.08
        shipping = 15.00 if subtotal < 50 else 0.00
        total = subtotal + tax + shipping

        return {
            "event_type": "purchase",
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session.session_id,
            "user_id": session.user_id,
            "session_state": session.state,
            "order_id": f"ord_{uuid.uuid4().hex[:8]}",
            "items": [
                {
                    "product_id": item["product_id"],
                    "product_name": item["name"],
                    "price": item["base_price"],
                    "quantity": 1,
                }
                for item in session.cart
            ],
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "shipping": shipping,
            "total": round(total, 2),
            "payment_method": random.choice(["credit_card", "debit_card", "paypal"]),
            "device": self.generate_device_info(),
            "geo": self.generate_geo_info(),
        }

    def _generate_session_end(self, session: UserSession) -> Dict[str, Any]:
        """Generate session end event."""
        duration = (datetime.now(timezone.utc) - session.start_time).total_seconds()

        return {
            "event_type": "session_end",
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session.session_id,
            "user_id": session.user_id,
            "session_state": session.state,
            "duration_seconds": int(duration),
            "pages_viewed": session.pages_viewed,
            "products_viewed": len(session.viewed_products),
            "items_in_cart": len(session.cart),
            "purchase_completed": session.state == "completed",
            "cart_abandoned": session.state == "abandoned",
            "abandonment_stage": session.state
            if session.state == "abandoned"
            else None,
            "device": self.generate_device_info(),
            "geo": self.generate_geo_info(),
        }
