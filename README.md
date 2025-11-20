# Real-Time E-Commerce Analytics Platform

A complete end-to-end real-time analytics pipeline for e-commerce data.

## Architecture

- **Event Streaming:** Apache Kafka
- **Stream Processing:** ksqlDB with Avro schemas
- **Schema Management:** Confluent Schema Registry
- **Data Integration:** Kafka Connect (JDBC Sink)
- **Storage:** PostgreSQL
- **Visualization:** Grafana

## Prerequisites

- Docker and Docker Compose
- Python 3.14+ (for data generator)
- Git

## Quick Start

### 1. Environment Setup

**IMPORTANT:** This project uses environment variables for sensitive credentials.

First, review and update the `.env` file that has been created:

```bash
# The .env file contains database passwords and admin credentials
# Update these values before running in production:
nano .env
```

Required environment variables:
- `POSTGRES_PASSWORD` - PostgreSQL database password
- `GRAFANA_ADMIN_PASSWORD` - Grafana admin password
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker addresses
- `KAFKA_TOPIC_EVENTS` - Event topic name

For development, the default values in `.env` are already set. For production:
1. Generate strong passwords for `POSTGRES_PASSWORD` and `GRAFANA_ADMIN_PASSWORD`
2. Never commit the `.env` file to version control (already in `.gitignore`)
3. Use a secrets management solution (e.g., AWS Secrets Manager, HashiCorp Vault)

### 2. Start Services

```bash
docker-compose up -d
```

This will start:
- Zookeeper (Kafka coordination)
- Kafka broker
- PostgreSQL database
- Schema Registry
- ksqlDB server
- Kafka Connect
- Grafana

### 3. Verify Services

Check that all services are running:
```bash
docker-compose ps
```

### 4. Generate Sample Data

```bash
source .venv/bin/activate
cd services/data-generator
python test_kafka_generator.py
```

### 5. Access Dashboards

- **Grafana:** http://localhost:3000
  - Username: `admin`
  - Password: Check your `.env` file (`GRAFANA_ADMIN_PASSWORD`)
- **ksqlDB:** http://localhost:8088
- **Schema Registry:** http://localhost:8081
- **Kafka Connect:** http://localhost:8083

## Dashboards

- **Session Overview:** User behavior, conversions, segments
- **Real-Time Activity:** Live event metrics
- **Product Analytics:** Revenue, AOV, cart abandonment

## Data Flow
```
Event Generator → Kafka → ksqlDB → Kafka Connect → PostgreSQL → Grafana
```

## Security Notes

1. **Credentials Management:**
   - All sensitive credentials are stored in `.env` file
   - `.env` is excluded from version control via `.gitignore`
   - Never commit credentials to the repository

2. **Default Passwords:**
   - Change default passwords before production deployment
   - Use strong, unique passwords for each service

3. **Network Security:**
   - Current setup uses PLAINTEXT Kafka (development only)
   - For production, enable SSL/TLS and SASL authentication
   - Use network segmentation and firewall rules

4. **Docker Security:**
   - Services run on isolated Docker network
   - Expose only necessary ports to host
   - Consider using Docker secrets for production

## Configuration

The data generator reads configuration from environment variables:

```python
from kafka_producer import EventProducer

# Automatically reads from KAFKA_BOOTSTRAP_SERVERS and KAFKA_TOPIC_EVENTS
producer = EventProducer()
```

Available environment variables:
- `KAFKA_BOOTSTRAP_SERVERS` - Comma-separated list of Kafka brokers
- `KAFKA_TOPIC_EVENTS` - Topic for event streaming
- `EVENT_GENERATION_MIN_DELAY` - Minimum delay between events (seconds)
- `EVENT_GENERATION_MAX_DELAY` - Maximum delay between events (seconds)
- `MAX_CONCURRENT_SESSIONS` - Maximum concurrent user sessions

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

### Kafka connection errors
Ensure `KAFKA_BOOTSTRAP_SERVERS` in your `.env` matches the Kafka service configuration:
- From host: `localhost:9092`
- From Docker containers: `kafka:9092`

### PostgreSQL connection errors
Verify credentials in `.env` match those in `docker-compose.yml`

