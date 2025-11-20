"""Kafka producer wrapper for event streaming."""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventProducer:
    """Kafka producer for streaming ecommerce events."""

    def __init__(
        self,
        bootstrap_servers: Optional[List[str]] = None,
        topic: Optional[str] = None,
        max_retries: int = 3
    ):
        """
        Initialize Kafka producer.

        Args:
            bootstrap_servers: List of Kafka broker addresses (defaults to env var KAFKA_BOOTSTRAP_SERVERS)
            topic: Default topic to publish to (defaults to env var KAFKA_TOPIC_EVENTS)
            max_retries: Maximum number of retries for failed sends
        """
        # Read from environment variables with defaults
        if bootstrap_servers is None:
            servers_str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            bootstrap_servers = [s.strip() for s in servers_str.split(",")]

        if topic is None:
            topic = os.getenv("KAFKA_TOPIC_EVENTS", "ecommerce.events")

        self.topic = topic
        self.events_sent = 0
        self.max_retries = max_retries

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",  # Wait for all replicas to acknowledge
                retries=max_retries,
                max_in_flight_requests_per_connection=1,  # Ensure ordering
                api_version=(0, 10, 1),
                request_timeout_ms=30000,  # 30 second timeout
                retry_backoff_ms=100,  # Backoff between retries
            )
            logger.info(f"Kafka producer connected to {bootstrap_servers}")
            logger.info(f"Publishing to topic: {topic}")

        except Exception as e:
            logger.error(f"Failed to create Kafka producer: {e}")
            raise

    def send_event(self, event: Dict[str, Any], key: str = None) -> bool:
        """
        Send event to Kafka topic.

        Args:
            event: Event dictionary to send
            key: Optional key for partitioning (e.g., session_id or user_id)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use session_id as key for partitioning (keeps session events together)
            if key is None:
                key = event.get("session_id", event.get("user_id"))

            # Send to Kafka
            future = self.producer.send(self.topic, value=event, key=key)

            # Optional: Wait for confirmation (for critical events)
            # record_metadata = future.get(timeout=10)

            self.events_sent += 1

            return True

        except KafkaError as e:
            logger.error(f"Kafka error sending event: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Error sending event: {e}", exc_info=True)
            return False

    def flush(self):
        """Flush any pending messages."""
        self.producer.flush()

    def close(self):
        """Close the producer connection."""
        self.producer.flush()
        self.producer.close()
        logger.info(f"Total events sent: {self.events_sent}")
        logger.info("Kafka producer closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
