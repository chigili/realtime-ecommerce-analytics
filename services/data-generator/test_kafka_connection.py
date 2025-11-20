"""Test Kafka connection and send a test message."""

import json
import time
from kafka import KafkaProducer
from kafka.errors import KafkaError


def test_kafka_connection():
    """Test connection to Kafka and send a test message."""

    print("🔍 Testing Kafka connection...")

    try:
        # Create Kafka producer
        producer = KafkaProducer(
            bootstrap_servers=["localhost:9092"],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            api_version=(0, 10, 1),
        )

        print("✅ Connected to Kafka!")

        # Send test message
        test_message = {
            "event_type": "test",
            "message": "Hello from Python!",
            "timestamp": time.time(),
        }

        print(f"\n📤 Sending test message: {test_message}")

        # Send to topic 'test-topic'
        future = producer.send("test-topic", test_message)

        # Wait for confirmation
        record_metadata = future.get(timeout=10)

        print(f"✅ Message sent successfully!")
        print(f"   Topic: {record_metadata.topic}")
        print(f"   Partition: {record_metadata.partition}")
        print(f"   Offset: {record_metadata.offset}")

        # Close producer
        producer.close()

        print("\n🎉 Kafka connection test PASSED!")
        return True

    except KafkaError as e:
        print(f"\n❌ Kafka Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    test_kafka_connection()
