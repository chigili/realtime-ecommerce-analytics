-- Create events table (raw events from Kafka)
CREATE TABLE IF NOT EXISTS events (
    event_id VARCHAR(50) PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    session_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    user_segment VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    -- Product info (nullable for non-product events)
    product_id VARCHAR(50),
    product_name VARCHAR(255),
    product_category VARCHAR(100),
    price DECIMAL(10, 2),

    -- Cart info
    cart_item_count INTEGER DEFAULT 0,
    cart_total DECIMAL(10, 2) DEFAULT 0,

    -- Additional metadata
    device_type VARCHAR(20),
    device_os VARCHAR(20),
    geo_country VARCHAR(10),
    geo_city VARCHAR(100),

    -- Indexes for fast queries
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);

-- Sessions table is auto-created by Kafka Connect from ksqlDB Avro schema
-- It will have uppercase column names: SESSION_ID, USER_ID, etc.
-- Do not create it manually here

-- Real-time metrics table (updated every minute by Flink)
CREATE TABLE IF NOT EXISTS metrics_realtime (
    metric_time TIMESTAMP PRIMARY KEY,

    -- Traffic metrics
    active_sessions INTEGER DEFAULT 0,
    total_events INTEGER DEFAULT 0,
    new_sessions INTEGER DEFAULT 0,

    -- User segment breakdown
    sessions_new INTEGER DEFAULT 0,
    sessions_returning INTEGER DEFAULT 0,
    sessions_vip INTEGER DEFAULT 0,
    sessions_churned INTEGER DEFAULT 0,

    -- Conversion metrics
    purchases_count INTEGER DEFAULT 0,
    revenue DECIMAL(12, 2) DEFAULT 0,
    avg_order_value DECIMAL(10, 2) DEFAULT 0,
    conversion_rate DECIMAL(5, 4) DEFAULT 0,

    -- Engagement metrics
    avg_session_duration INTEGER DEFAULT 0,
    avg_events_per_session DECIMAL(5, 2) DEFAULT 0,

    -- Abandonment
    cart_abandonments INTEGER DEFAULT 0,
    checkout_abandonments INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_metrics_time ON metrics_realtime(metric_time DESC);

-- Product performance table
CREATE TABLE IF NOT EXISTS product_metrics (
    product_id VARCHAR(50),
    hour TIMESTAMP,

    views_count INTEGER DEFAULT 0,
    add_to_cart_count INTEGER DEFAULT 0,
    purchase_count INTEGER DEFAULT 0,
    revenue DECIMAL(10, 2) DEFAULT 0,

    PRIMARY KEY (product_id, hour)
);

-- Hourly aggregations table
CREATE TABLE IF NOT EXISTS hourly_metrics (
    hour TIMESTAMP PRIMARY KEY,

    total_sessions INTEGER DEFAULT 0,
    total_events INTEGER DEFAULT 0,
    total_purchases INTEGER DEFAULT 0,
    total_revenue DECIMAL(12, 2) DEFAULT 0,
    avg_conversion_rate DECIMAL(5, 4) DEFAULT 0,

    -- Segment breakdown
    sessions_by_segment JSONB,
    revenue_by_segment JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);