"""Test event generator with Kafka integration."""

import random
import time
from collections import defaultdict

from src.generators.base import UserGenerator
from src.generators.event_generator import EventGenerator
from src.generators.product import ProductGenerator
from src.generators.session import SessionManager
from src.kafka_producer import EventProducer


def main():
    """Test event generation with Kafka publishing."""

    print("🚀 Initializing generators...")

    # Initialize generators
    users = UserGenerator(num_users=100, seed=42)
    products = ProductGenerator(num_products=50, seed=42)

    print(f"✅ Generated {len(users._user_cache)} users")
    print(f"✅ Generated {len(products._product_cache)} products\n")

    # Initialize session manager and event generator
    session_manager = SessionManager(users, products, max_concurrent_sessions=5)
    event_gen = EventGenerator(users, products)

    # Initialize Kafka producer
    print("🔌 Connecting to Kafka...")
    kafka_producer = EventProducer(
        bootstrap_servers=["localhost:9092"], topic="ecommerce.events"
    )
    print()

    # Stats
    events_by_type = defaultdict(int)
    sessions_by_outcome = defaultdict(int)
    purchase_count = 0
    start_time = time.time()

    print("📊 Generating events and publishing to Kafka...")
    print("Press Ctrl+C to stop\n")
    print("=" * 80)

    try:
        # Generate events for 5 minutes (or until Ctrl+C)
        event_count = 0
        max_events = 100  # Generate 100 events for testing

        while event_count < max_events:
            # Get session
            session = session_manager.get_or_create_session()

            # Generate event
            event = event_gen.generate_next_event(session)

            event_type = event["event_type"]
            events_by_type[event_type] += 1

            # Send to Kafka
            success = kafka_producer.send_event(event)

            # State emoji
            state_emoji = {
                "browsing": "👀",
                "shopping": "🛍️",
                "checkout": "💳",
                "completed": "✅",
                "abandoned": "❌",
            }

            emoji = state_emoji.get(session.state, "❓")

            # Track outcomes
            if event_type == "purchase":
                purchase_count += 1
                sessions_by_outcome["completed"] += 1
            elif event_type == "session_end":
                if event.get("purchase_completed"):
                    sessions_by_outcome["completed"] += 1
                else:
                    sessions_by_outcome[f"abandoned_{session.state}"] += 1

                session_manager.end_session(session.session_id)

            # Print event (with Kafka status)
            kafka_status = "✅" if success else "❌"
            print(
                f"{kafka_status} [{event_type:18}] {emoji} {session.state:10} | "
                f"Seg:{session.user_segment:8} | "
                f"Sess:{session.session_id[:8]} | "
                f"Evt:{session.events_generated:2} | "
                f"View:{len(session.viewed_products)} Cart:{len(session.cart)}",
                end="",
            )

            if event_type == "purchase":
                print(f" | 💰 ${event.get('total', 0):.2f}")
            elif event_type == "session_end":
                print(f" | {event.get('duration_seconds', 0)}s")
            else:
                print()

            event_count += 1

            # Realistic timing - 1-3 seconds between events
            time.sleep(random.uniform(1.0, 3.0))

    except KeyboardInterrupt:
        print("\n\n⚠️  Stopped by user")

    # Close Kafka producer
    print("\n🔌 Closing Kafka connection...")
    kafka_producer.close()

    # Summary
    elapsed = time.time() - start_time
    total_events = sum(events_by_type.values())
    total_sessions = sum(sessions_by_outcome.values())

    print("\n" + "=" * 80)
    print("📈 FINAL SUMMARY")
    print("=" * 80)

    print(f"\n⏱️  TIME:")
    print(f"  Duration: {elapsed:.1f}s")
    print(f"  Total events: {total_events:,}")
    print(f"  Rate: {total_events / elapsed:.1f} events/sec")

    print(f"\n📊 EVENT BREAKDOWN:")
    for event_type, count in sorted(events_by_type.items(), key=lambda x: -x[1]):
        pct = count / total_events * 100 if total_events > 0 else 0
        print(f"  {event_type:20}: {count:4} ({pct:5.1f}%)")

    print(f"\n🎯 SESSIONS:")
    print(f"  Total created: {session_manager.total_sessions_created}")
    print(f"  Ended: {total_sessions}")
    print(f"  Active: {session_manager.get_active_session_count()}")

    if total_sessions > 0:
        completed = sessions_by_outcome.get("completed", 0)
        conversion = (completed / total_sessions) * 100
        print(f"\n  ✅ Purchases: {purchase_count} ({conversion:.1f}% conversion)")

        total_abandoned = sum(
            count
            for key, count in sessions_by_outcome.items()
            if key.startswith("abandoned_")
        )

        if total_abandoned > 0:
            print(
                f"\n  ❌ Abandonment: {total_abandoned} ({total_abandoned / total_sessions * 100:.1f}%)"
            )
            print(f"     By stage:")
            for key, count in sorted(sessions_by_outcome.items()):
                if key.startswith("abandoned_"):
                    stage = key.replace("abandoned_", "")
                    pct = (count / total_sessions) * 100
                    print(f"       {stage:12}: {count:3} ({pct:5.1f}%)")


if __name__ == "__main__":
    main()
