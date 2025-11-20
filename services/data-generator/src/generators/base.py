"""Base generator classes."""

from abc import ABC, abstractmethod
from faker import Faker
import random
from typing import Dict, List, Any, Optional


class BaseGenerator(ABC):
    """Base class for all generators."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator."""
        self.fake = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)

    @abstractmethod
    def generate(self) -> Dict[str, Any]:
        """Generate data."""
        pass


class UserGenerator(BaseGenerator):
    """Generate user data."""

    def __init__(self, num_users: int = 10000, seed: Optional[int] = None):
        super().__init__(seed)
        self.num_users = num_users
        self._user_cache = {}
        self._generate_users()

    def _generate_users(self):
        """Pre-generate users."""
        user_segments = {"new": 0.40, "returning": 0.45, "vip": 0.10, "churned": 0.05}

        for i in range(self.num_users):
            user_id = f"user_{i:05d}"
            segment = random.choices(
                list(user_segments.keys()), weights=list(user_segments.values())
            )[0]

            self._user_cache[user_id] = {
                "user_id": user_id,
                "segment": segment,
                "signup_date": self.fake.date_between(
                    start_date="-2y", end_date="today"
                ),
                "total_orders": self._get_orders_by_segment(segment),
                "lifetime_value": 0.0,
                "country": random.choices(
                    ["US", "UK", "CA", "DE", "FR"],
                    weights=[0.60, 0.15, 0.10, 0.08, 0.07],
                )[0],
            }

    def _get_orders_by_segment(self, segment: str) -> int:
        """Get typical order count by segment."""
        orders = {
            "new": random.randint(0, 1),
            "returning": random.randint(2, 10),
            "vip": random.randint(10, 50),
            "churned": random.randint(1, 5),
        }
        return orders[segment]

    def get_random_user(self) -> Dict[str, Any]:
        """Get a random user."""
        user_id = random.choice(list(self._user_cache.keys()))
        return self._user_cache[user_id]

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get specific user."""
        return self._user_cache.get(user_id)

    def generate(self) -> Dict[str, Any]:
        """Generate a user (for ABC compliance)."""
        return self.get_random_user()
