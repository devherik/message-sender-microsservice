
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
