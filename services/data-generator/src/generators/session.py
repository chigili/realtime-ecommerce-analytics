"""Session management for realistic user behavior - FIXED VERSION."""

import random
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class UserSession:
    """Represents an active user session."""

    session_id: str
    user_id: str
    user_segment: str
    start_time: datetime

    # Session state
    state: str = "browsing"  # browsing, shopping, checkout, completed, abandoned
    cart: List[Dict] = field(default_factory=list)
    viewed_products: List[str] = field(default_factory=list)
    searches: List[str] = field(default_factory=list)
    pages_viewed: int = 0

    # Behavior tracking
    current_page: Optional[str] = None
    last_event_time: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    events_generated: int = 0

    # Session goals (predefined at creation)
    will_purchase: bool = False
    target_session_duration: int = 300  # seconds
    target_pages: int = 10

    def is_expired(self) -> bool:
        """
        Check if session should end.
        FIXED: Proper timing and probabilistic ending.
        """
        # Completed purchases end immediately
        if self.state == "completed":
            return True

        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        # Natural time-based expiry (ONLY if exceeded target duration)
        if elapsed > self.target_session_duration:
            if self.state not in ["completed", "abandoned"]:
                self.state = "abandoned"
            return True

        # Idle timeout (10 minutes of inactivity)
        idle_time = (datetime.now(timezone.utc) - self.last_event_time).total_seconds()
        if idle_time > 600:
            if self.state not in ["completed", "abandoned"]:
                self.state = "abandoned"
            return True

        # Probabilistic session end (more realistic)
        if self.events_generated >= self.target_pages * 0.5:
            progress = min(self.events_generated / self.target_pages, 1.5)

            # Gradually increasing probability to end
            # At 50% progress: 0% chance to end
            # At 100% progress: 20% chance to end per event
            # At 150% progress: 40% chance to end per event
            end_probability = max(0, (progress - 0.5) * 0.4)

            if random.random() < end_probability:
                if self.state not in ["completed", "abandoned"]:
                    self.state = "abandoned"
                return True

        return False

    def get_cart_value(self) -> float:
        """Calculate total cart value."""
        return sum(item.get("base_price", 0) for item in self.cart)

    def get_session_quality_score(self) -> float:
        """
        Calculate session quality score (0-10).
        Used for analytics.
        """
        score = 0.0

        # Engagement indicators
        if self.events_generated > 5:
            score += 2.0
        if len(self.viewed_products) > 3:
            score += 2.0
        if len(self.searches) > 0:
            score += 1.0
        if len(self.cart) > 0:
            score += 2.0
        if self.state == "checkout":
            score += 1.5
        if self.state == "completed":
            score += 1.5

        return min(score, 10.0)


class SessionManager:
    """Manages active user sessions."""

    def __init__(
        self, user_generator, product_generator, max_concurrent_sessions: int = 20
    ):
        """Initialize session manager."""
        self.user_generator = user_generator
        self.product_generator = product_generator
        self.max_concurrent_sessions = max_concurrent_sessions

        self.active_sessions: Dict[str, UserSession] = {}
        self.total_sessions_created = 0
        self.current_session: Optional[UserSession] = None
        self.events_on_current_session = 0
        self.max_events_per_session = (
            8  # Generate 5-10 events per session before switching
        )

    def get_or_create_session(self) -> UserSession:
        """
        Get an active session or create a new one.
        Stick with sessions for multiple events to see full journeys.
        """
        # Clean up expired sessions
        self._cleanup_expired_sessions()

        # If we have a current session and haven't generated enough events, keep using it
        if (
            self.current_session
            and not self.current_session.is_expired()
            and self.events_on_current_session < self.max_events_per_session
        ):
            self.events_on_current_session += 1
            return self.current_session

        # Time to switch sessions
        self.events_on_current_session = 1

        # Vary the max events per session (5-10) for realism
        self.max_events_per_session = random.randint(5, 10)

        # 30% chance to pick an existing active session (simulate returning to other users)
        if self.active_sessions and random.random() < 0.3:
            self.current_session = random.choice(list(self.active_sessions.values()))
            return self.current_session

        # Create new session if under limit
        if len(self.active_sessions) < self.max_concurrent_sessions:
            self.current_session = self._create_new_session()
            return self.current_session

        # Otherwise pick an existing session
        self.current_session = random.choice(list(self.active_sessions.values()))
        return self.current_session

    def _create_new_session(self) -> UserSession:
        """Create a new user session with realistic parameters."""
        user = self.user_generator.get_random_user()
        session_id = f"sess_{uuid.uuid4().hex[:12]}"

        # Get behavior parameters based on user segment
        behavior = self._get_segment_behavior(user["segment"])

        # Determine if this user will purchase
        # This is their INTENT, but they might still abandon due to other factors
        will_purchase = random.random() < behavior["conversion_intent"]

        session = UserSession(
            session_id=session_id,
            user_id=user["user_id"],
            user_segment=user["segment"],
            start_time=datetime.now(timezone.utc),
            will_purchase=will_purchase,
            target_session_duration=random.randint(*behavior["session_duration"]),
            target_pages=random.randint(
                behavior["pages_per_session"][0] * 3,
                behavior["pages_per_session"][1] * 3,
            ),
        )

        self.active_sessions[session_id] = session
        self.total_sessions_created += 1

        return session

    def _get_segment_behavior(self, segment: str) -> Dict[str, Any]:
        """
        Get behavior parameters for user segment.

        Note: conversion_intent is INTENT to purchase, not actual conversion rate.
        Actual conversion is lower due to abandonment.
        """
        behaviors = {
            "new": {
                "session_duration": (120, 300),  # 2-5 minutes
                "pages_per_session": (3, 10),
                "conversion_intent": 0.10,  # 10% INTEND to buy
                # But due to abandonment, only ~2% actually complete
                "avg_cart_items": (1, 2),
            },
            "returning": {
                "session_duration": (300, 600),  # 5-10 minutes
                "pages_per_session": (5, 15),
                "conversion_intent": 0.20,  # 20% INTEND to buy
                # Actual: ~5-8% complete
                "avg_cart_items": (1, 3),
            },
            "vip": {
                "session_duration": (180, 480),  # 3-8 minutes
                "pages_per_session": (4, 12),
                "conversion_intent": 0.50,  # 50% INTEND to buy
                # Actual: ~25-35% complete (high!)
                "avg_cart_items": (2, 5),
            },
            "churned": {
                "session_duration": (60, 180),  # 1-3 minutes (short)
                "pages_per_session": (2, 6),
                "conversion_intent": 0.05,  # 5% INTEND to buy
                # Actual: <1% complete
                "avg_cart_items": (1, 1),
            },
        }
        return behaviors.get(segment, behaviors["returning"])

    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        expired = [
            sid for sid, session in self.active_sessions.items() if session.is_expired()
        ]
        for sid in expired:
            # If we're currently on an expired session, clear it
            if self.current_session and self.current_session.session_id == sid:
                self.current_session = None
                self.events_on_current_session = 0
            del self.active_sessions[sid]

    def get_active_session_count(self) -> int:
        """Get count of active sessions."""
        return len(self.active_sessions)

    def end_session(self, session_id: str):
        """Explicitly end a session (called when session_end event generated)."""
        if session_id in self.active_sessions:
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session = None
                self.events_on_current_session = 0
            del self.active_sessions[session_id]

    def get_session_stats(self) -> Dict[str, int]:
        """Get statistics about sessions by state."""
        stats = {
            "browsing": 0,
            "shopping": 0,
            "checkout": 0,
            "completed": 0,
            "abandoned": 0,
        }
        for session in self.active_sessions.values():
            stats[session.state] = stats.get(session.state, 0) + 1
        return stats

    def get_segment_stats(self) -> Dict[str, int]:
        """Get statistics about sessions by user segment."""
        stats = {"new": 0, "returning": 0, "vip": 0, "churned": 0}
        for session in self.active_sessions.values():
            stats[session.user_segment] = stats.get(session.user_segment, 0) + 1
        return stats

    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed statistics about all sessions."""
        total_sessions = len(self.active_sessions)

        if total_sessions == 0:
            return {"total_active": 0, "total_created": self.total_sessions_created}

        # Aggregate stats
        total_events = sum(s.events_generated for s in self.active_sessions.values())
        total_products_viewed = sum(
            len(s.viewed_products) for s in self.active_sessions.values()
        )
        total_in_cart = sum(len(s.cart) for s in self.active_sessions.values())
        sessions_with_cart = sum(
            1 for s in self.active_sessions.values() if len(s.cart) > 0
        )

        return {
            "total_active": total_sessions,
            "total_created": self.total_sessions_created,
            "avg_events_per_session": total_events / total_sessions
            if total_sessions > 0
            else 0,
            "avg_products_viewed": total_products_viewed / total_sessions
            if total_sessions > 0
            else 0,
            "sessions_with_cart": sessions_with_cart,
            "total_items_in_carts": total_in_cart,
            "by_state": self.get_session_stats(),
            "by_segment": self.get_segment_stats(),
        }
