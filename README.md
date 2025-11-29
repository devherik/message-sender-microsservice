# Versatile Data Ingestion Platform

A production-ready **data ingestion and analytics platform** built with **Clean Architecture** principles. This microservice can receive data from N applications, apply routing rules, persist to database, and provide comprehensive statistics.

## 🚀 What's New in v0.2.0

### Universal Data Ingestion
- **Accept ANY data type** from ANY application via flexible JSON payloads
- **No code changes needed** for new event types
- **Automatic metadata enrichment** (IP, user-agent, correlation ID)

### Intelligent Routing
- **Configurable routing rules** stored in database
- **Condition-based matching** with operators (`$gt`, `$lt`, `$eq`, etc.)
- **Priority-based execution** for complex routing scenarios
- **Multiple destination types**: webhooks, database tables, message queues

### Comprehensive Analytics
- **Pre-aggregated statistics** for fast dashboard queries
- **Flexible time periods**: hourly, daily, weekly
- **Event-type filtering** for detailed analysis
- **Real-time metrics** with manual refresh capability

---

## Architecture Overview

This project implements **Clean Architecture** with strict adherence to **SOLID principles**, ensuring maintainability, testability, and scalability.

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│         (FastAPI Routers - REST API Endpoints)           │
│   /api/ingest  |  /api/routing-rules  |  /api/statistics │
└────────────────────┬────────────────────────────────────┘
                     │ depends on ↓
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│              (Use Cases / Services)                      │
│  DataIngestionService | RoutingService | StatisticsService │
└────────────────────┬────────────────────────────────────┘
                     │ depends on ↓
┌─────────────────────────────────────────────────────────┐
│                     Domain Layer                         │
│         (Entities, Interfaces, Business Rules)           │
│   DataEvent | RoutingRule | EventStatistics              │
└─────────────────────────────────────────────────────────┘
                     ↑ implemented by
┌─────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                     │
│         (PostgreSQL Repositories, External APIs)         │
└─────────────────────────────────────────────────────────┘
```

---

## Core Features

### 1. Universal Data Ingestion
```bash
POST /api/ingest/{app_id}
{
  "event_type": "order_created",
  "payload": {
    "order_id": "ORD-123",
    "customer_id": 456,
    "total": 99.99
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Data ingested successfully",
  "data": {
    "event_id": 789,
    "routing_summary": {
      "rules_evaluated": 2,
      "rules_matched": 1,
      "rules_executed": 1
    }
  }
}
```

### 2. Routing Rules Management

Create rules to automatically route data:

```bash
POST /api/routing-rules
{
  "app_id": 1,
  "rule_name": "Forward high-value orders",
  "event_type_filter": "order_created",
  "condition": {"payload.total": {"$gt": 50}},
  "destination_type": "webhook",
  "destination_config": {"url": "https://example.com/webhook"},
  "priority": 10
}
```

**Supported Operators:**
- `$gt` - Greater than
- `$lt` - Less than
- `$gte` - Greater than or equal
- `$lte` - Less than or equal
- `$eq` - Equal
- `$ne` - Not equal
- `$exists` - Field exists

### 3. Analytics & Statistics

Get aggregated metrics:

```bash
GET /api/statistics/1?time_period=daily&event_type=order_created
```

**Dashboard Metrics:**
```bash
GET /api/statistics/dashboard/1?time_period=daily
```

Returns summary across all event types with totals.

---

## Technology Stack

**Core Framework:**
- FastAPI 0.120.4 - Modern async web framework
- Python 3.12+ - Latest features and performance
- Uvicorn - High-performance ASGI server

**Data & Persistence:**
- PostgreSQL - Primary database with JSONB support
- psycopg2 - Database adapter with connection pooling
- GIN indexes - Optimized JSONB querying

**Architecture:**
- Pydantic v2 - Data validation and serialization
- ABC (Abstract Base Classes) - Interface definitions
- Dependency Injection - Clean component composition

---

## Project Structure

```
message-sender-microsservice/
├── models/                        # Domain Layer
│   ├── models.py                 # Legacy message entities
│   ├── data_events.py            # NEW: Generic data entities
│   └── interfaces.py             # Repository interfaces (DIP)
├── services/                      # Application Layer
│   ├── data_ingestion_service.py # NEW: Data ingestion use case
│   ├── routing_service.py        # NEW: Routing logic
│   ├── statistics_service.py     # NEW: Analytics use case
│   └── routing_rule_service.py   # NEW: Rule management
├── repositories/                  # Infrastructure Layer
│   ├── data_event_repository.py  # NEW: Event persistence
│   ├── routing_rule_repository.py # NEW: Rule persistence
│   ├── statistics_repository.py  # NEW: Analytics queries
│   └── postgres_repository.py    # Database connection
├── routers/                       # Presentation Layer
│   ├── data_ingestion_router.py  # NEW: Ingestion endpoints
│   ├── routing_rules_router.py   # NEW: Rule management endpoints
│   ├── statistics_router.py      # NEW: Analytics endpoints
│   ├── message_router.py         # Legacy message endpoints
│   └── test_router.py
├── database/
│   └── schema.sql                # Database schema with new tables
└── main.py                        # Application entry point
```

---

## API Endpoints

### Data Ingestion
- `POST /api/ingest/{app_id}` - Ingest any data event
- `GET /api/events/{event_id}` - Retrieve specific event
- `GET /api/events/app/{app_id}` - List events for application

### Routing Rules
- `POST /api/routing-rules` - Create routing rule
- `GET /api/routing-rules/{rule_id}` - Get rule by ID
- `GET /api/routing-rules/app/{app_id}` - List rules for application
- `PUT /api/routing-rules/{rule_id}` - Update rule
- `DELETE /api/routing-rules/{rule_id}` - Delete rule
- `PATCH /api/routing-rules/{rule_id}/toggle` - Enable/disable rule

### Statistics
- `GET /api/statistics/{app_id}` - Get aggregated statistics
- `GET /api/statistics/dashboard/{app_id}` - Dashboard metrics
- `POST /api/statistics/refresh/{app_id}` - Manually refresh stats

### Legacy (Backward Compatible)
- `POST /api/messages/{app_id}` - Create message
- `GET /` - Health check with database status
- `GET /health` - Simple health check

---

## Database Schema

### New Tables

**data_events** - Universal event storage
```sql
CREATE TABLE data_events (
    event_id SERIAL PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES applications(app_id),
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**routing_rules** - Routing configurations
```sql
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**event_statistics** - Pre-aggregated metrics
```sql
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
    UNIQUE(app_id, event_type, time_bucket, time_period)
);
```

**Performance Indexes:**
- GIN indexes on JSONB columns for fast querying
- B-tree indexes on app_id, event_type, created_at
- Composite indexes for common query patterns

---

## Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL 14+

### Installation

1. Clone and setup:
```bash
git clone https://github.com/devherik/message-sender-microsservice.git
cd message-sender-microsservice
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. Initialize database:
```bash
psql -U postgres -f database/schema.sql
```

4. Run the application:
```bash
uvicorn main:app --reload
```

5. Access API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Design Patterns & Principles

### SOLID Principles

**Single Responsibility (SRP)**
- Each service has one clear purpose
- `DataIngestionService` handles ingestion only
- `RoutingService` handles routing only
- `StatisticsService` handles analytics only

**Open/Closed (OCP)**
- System is open for extension via new event types
- Closed for modification - no code changes needed
- New routing strategies added via configuration

**Dependency Inversion (DIP)**
- Services depend on interfaces, not implementations
- Easy testing with mocks
- Can swap PostgreSQL for another database

**Interface Segregation (ISP)**
- Focused interfaces for each repository
- Clients only depend on methods they use

### Design Patterns

1. **Repository Pattern** - Data access abstraction
2. **Strategy Pattern** - Pluggable routing strategies
3. **Dependency Injection** - Loose coupling
4. **CQRS** - Separate read/write models for statistics

---

## Why This Architecture?

1. **Flexibility** - Accept any data type without code changes
2. **Testability** - Interface-based design enables easy mocking
3. **Maintainability** - Clear separation of concerns
4. **Scalability** - Stateless design, horizontal scaling ready
5. **Observability** - Built-in metadata tracking and correlation IDs

---

## Example Use Cases

### E-commerce Platform
```python
# Ingest order events
POST /api/ingest/1
{"event_type": "order_created", "payload": {"order_id": "123", "total": 99.99}}

# Route high-value orders to fulfillment webhook
POST /api/routing-rules
{"condition": {"payload.total": {"$gt": 50}}, "destination_type": "webhook"}

# Track order statistics
GET /api/statistics/1?event_type=order_created&time_period=daily
```

### User Analytics
```python
# Track user actions
POST /api/ingest/2
{"event_type": "user_login", "payload": {"user_id": 456, "device": "mobile"}}

# Get user activity metrics
GET /api/statistics/dashboard/2?time_period=hourly
```

---

## Contributing

This is a portfolio project demonstrating software engineering best practices. Suggestions and feedback are welcome!

## License

Available for review and educational purposes.

## Contact

**Herik Rezende**
- GitHub: [@devherik](https://github.com/devherik)
- LinkedIn: [Connect with me](https://linkedin.com/in/herikrezende)

---

**Built with Clean Architecture, SOLID principles, and a passion for well-designed systems.**
