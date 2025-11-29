
CREATE TABLE applications (
    app_id SERIAL PRIMARY KEY,
    app_name VARCHAR(255) NOT NULL UNIQUE,
    api_key VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE phone_numbers (
    phone_number_id SERIAL PRIMARY KEY,
    phone_number VARCHAR(50) NOT NULL UNIQUE,
    app_id INTEGER REFERENCES applications(app_id),
    is_webhook BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES applications(app_id),
    sender_phone_number_id INTEGER NOT NULL REFERENCES phone_numbers(phone_number_id),
    recipient_phone_number VARCHAR(50) NOT NULL,
    message_content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    scheduled_for TIMESTAMP WITH TIME ZONE
);

CREATE TABLE message_logs (
    log_id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(message_id),
    log_message VARCHAR(255) NOT NULL,
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE message_metrics (
    metric_id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(message_id),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    processing_time_ms INTEGER
);

CREATE TABLE webhooks (
    webhook_id SERIAL PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES applications(app_id),
    webhook_url VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- e.g., 'message_sent', 'message_delivered'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_messages_status ON messages(status);
CREATE INDEX idx_messages_app_id ON messages(app_id);
CREATE INDEX idx_message_logs_message_id ON message_logs(message_id);
CREATE INDEX idx_message_metrics_message_id ON message_metrics(message_id);
CREATE INDEX idx_webhooks_app_id ON webhooks(app_id);

-- ============================================================
-- Data Ingestion Platform Tables
-- ============================================================

-- Generic data events table for flexible ingestion from N applications
CREATE TABLE data_events (
    event_id SERIAL PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES applications(app_id),
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Routing rules for data redirection
CREATE TABLE routing_rules (
    rule_id SERIAL PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES applications(app_id),
    rule_name VARCHAR(255) NOT NULL,
    event_type_filter VARCHAR(100),
    condition JSONB NOT NULL,
    destination_type VARCHAR(50) NOT NULL,
    destination_config JSONB NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Pre-aggregated statistics for analytics
CREATE TABLE event_statistics (
    stat_id SERIAL PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES applications(app_id),
    event_type VARCHAR(100) NOT NULL,
    total_events INTEGER DEFAULT 0,
    processed_events INTEGER DEFAULT 0,
    failed_events INTEGER DEFAULT 0,
    pending_events INTEGER DEFAULT 0,
    time_bucket TIMESTAMP WITH TIME ZONE NOT NULL,
    time_period VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(app_id, event_type, time_bucket, time_period)
);

-- Performance indexes for data ingestion platform
CREATE INDEX idx_data_events_app_id ON data_events(app_id);
CREATE INDEX idx_data_events_event_type ON data_events(event_type);
CREATE INDEX idx_data_events_created_at ON data_events(created_at);
CREATE INDEX idx_data_events_processed ON data_events(processed);
CREATE INDEX idx_data_events_payload ON data_events USING GIN(payload);
CREATE INDEX idx_data_events_metadata ON data_events USING GIN(metadata);
CREATE INDEX idx_routing_rules_app_id ON routing_rules(app_id);
CREATE INDEX idx_routing_rules_active ON routing_rules(is_active);
CREATE INDEX idx_routing_rules_event_type ON routing_rules(event_type_filter);
CREATE INDEX idx_event_statistics_lookup ON event_statistics(app_id, event_type, time_bucket);
CREATE INDEX idx_event_statistics_time_period ON event_statistics(time_period, time_bucket);
