# Message Sender Microservice

A production-ready messaging microservice built with **Clean Architecture** principles, demonstrating advanced software engineering practices and modern Python development.

## Architecture Overview

This project implements **Clean Architecture** with strict adherence to **SOLID principles**, ensuring maintainability, testability, and scalability. The architecture separates concerns into distinct layers with well-defined boundaries and dependencies flowing inward.

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│              (FastAPI Routers & Endpoints)               │
└────────────────────┬────────────────────────────────────┘
                     │ depends on ↓
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│        (Use Cases / Business Logic / Services)           │
└────────────────────┬────────────────────────────────────┘
                     │ depends on ↓
┌─────────────────────────────────────────────────────────┐
│                     Domain Layer                         │
│              (Entities, Interfaces, Models)              │
└─────────────────────────────────────────────────────────┘
                     ↑ implemented by
┌─────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                     │
│         (Database, External APIs, Frameworks)            │
└─────────────────────────────────────────────────────────┘
```

## Key Technical Highlights

### Clean Architecture Implementation

- **Dependency Inversion Principle (DIP)**: High-level modules (services) depend on abstractions (`IDatabaseRepository` interface) rather than concrete implementations
- **Single Responsibility Principle (SRP)**: Each component has one clear purpose - repositories handle data persistence, services contain business logic, routers manage HTTP concerns
- **Open/Closed Principle (OCP)**: The system is open for extension through interfaces while closed for modification
- **Interface Segregation**: Clean, focused interfaces that define clear contracts between layers

### Advanced Python Features

- **Strong Type Hinting**: Comprehensive type annotations throughout the codebase
- **Pydantic Models**: Data validation and serialization with Pydantic v2
- **Abstract Base Classes (ABC)**: Formal interface definitions enforcing contracts
- **Async Context Managers**: Proper resource management with lifespan events
- **Dependency Injection**: FastAPI's DI system used for clean component composition

### Production-Ready Patterns

- **Connection Pooling Strategy**: Proper database connection lifecycle management
- **Retry Logic**: Automatic retry mechanism for transient database failures
- **Correlation IDs**: Request tracing middleware for distributed system observability
- **Structured Logging**: Contextual logging with correlation ID propagation
- **Configuration Management**: Environment-based settings with Pydantic Settings
- **Health Checks**: Comprehensive health endpoint with database status verification

## Technology Stack

**Core Framework:**
- FastAPI 0.120.4 - Modern async web framework
- Python 3.12+ - Latest Python features and performance improvements
- Uvicorn - High-performance ASGI server

**Data & Persistence:**
- PostgreSQL - Primary relational database
- psycopg2 - Database adapter with connection management
- pgvector - Vector similarity search support

**AI/ML Integration:**
- Agno Framework - AI agent orchestration
- Google GenAI - LLM integration capabilities

**Task Processing:**
- Celery - Distributed task queue for async operations
- Redis - Message broker and caching layer

**Security & Authentication:**
- python-jose - JWT token handling
- bcrypt - Password hashing

**Code Quality:**
- Pydantic - Data validation and settings management
- Python type hints - Static type checking support

## Project Structure

```
message-sender-microsservice/
├── core/                          # Application core configuration
│   ├── dependencies.py           # Dependency injection setup
│   ├── security.py               # Authentication & authorization
│   └── settings.py               # Environment configuration
├── models/                        # Domain layer
│   ├── interfaces.py             # Abstract interfaces (DIP)
│   └── models.py                 # Domain entities & DTOs
├── services/                      # Application layer (use cases)
│   └── message_service.py        # Business logic orchestration
├── repositories/                  # Infrastructure layer
│   ├── message_sender_repository.py
│   └── postgres_repository.py    # Concrete DB implementation
├── routers/                       # Presentation layer
│   └── message_router.py         # HTTP endpoints
├── middlewares/                   # Cross-cutting concerns
│   └── correlation_id_mw.py      # Request tracing
├── database/
│   └── schema.sql                # Database schema definition
├── helpers/                       # Utilities
│   ├── logging_helper.py
│   └── dotenv_load_helper.py
└── tests/                         # Test suite
    ├── database_tests.py
    └── waha_api_test.py
```

## Core Features

### Message Management
- **Asynchronous Message Processing**: Non-blocking message creation and delivery
- **Multi-Application Support**: Isolated message queues per application
- **Message Logging**: Comprehensive audit trail of message lifecycle
- **Metrics Collection**: Performance tracking and delivery analytics
- **Webhook Integration**: Event-driven notifications for message status

### Observability
- **Correlation ID Tracking**: End-to-end request tracing across services
- **Structured Logging**: Context-rich logs for debugging and monitoring
- **Health Endpoints**: System status and dependency health checks
- **Metrics Storage**: Historical data for performance analysis

### Data Model

The system manages multiple entities with proper relational integrity:

- **Applications**: Multi-tenant support with API key authentication
- **Phone Numbers**: Sender identity management with webhook configuration
- **Messages**: Core messaging entity with status tracking
- **Message Logs**: Audit trail for compliance and debugging
- **Message Metrics**: Performance and delivery statistics
- **Webhooks**: Event notification configuration

## Design Patterns Demonstrated

1. **Repository Pattern**: Abstracts data access logic from business logic
2. **Dependency Injection**: Loose coupling through constructor injection
3. **Strategy Pattern**: Swappable database implementations via interfaces
4. **Factory Pattern**: Service creation through dependency functions
5. **Middleware Pattern**: Cross-cutting concerns handled elegantly
6. **Circuit Breaker**: Retry logic prevents cascading failures

## Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL 14+
- Redis 7+ (for Celery)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/devherik/message-sender-microsservice.git
cd message-sender-microsservice
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Set up the database:
```bash
psql -U postgres -f database/schema.sql
```

5. Run the application:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, access the interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Health Check
```http
GET /
```
Returns service status and database connectivity information.

### Create Message
```http
POST /api/messages/{app_id}
```
Creates a new message for the specified application.

**Request Body:**
```json
{
  "message_content": "Your message here"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Message created successfully",
  "data": {
    "message_id": 123
  }
}
```

## Development Practices

### Code Quality
- **Type Safety**: Comprehensive type hints throughout the codebase
- **Data Validation**: Pydantic models ensure data integrity at boundaries
- **Error Handling**: Explicit exception handling with proper propagation
- **Separation of Concerns**: Clear boundaries between layers

### Testing Strategy
- **Unit Tests**: Business logic tested in isolation
- **Integration Tests**: Database and external API testing
- **Mock Dependencies**: Interface-based mocking for clean tests

### Configuration Management
- **Environment-Based**: Separate configs for dev/staging/production
- **Type-Safe Settings**: Pydantic Settings for validation
- **Secrets Management**: Secure handling of sensitive configuration

## Why This Architecture?

This project demonstrates key principles that scale from startups to enterprise:

1. **Testability**: Interface-based design allows easy mocking and unit testing
2. **Maintainability**: Clear separation of concerns makes changes predictable
3. **Flexibility**: New features can be added without modifying existing code
4. **Scalability**: Stateless design enables horizontal scaling
5. **Team Collaboration**: Well-defined boundaries reduce merge conflicts

## Future Enhancements

- [ ] Implement message scheduling functionality
- [ ] Add rate limiting per application
- [ ] Implement retry policies for failed deliveries
- [ ] Add support for message templates
- [ ] Implement WebSocket support for real-time updates
- [ ] Add comprehensive monitoring with Prometheus/Grafana
- [ ] Implement Circuit Breaker pattern for external API calls
- [ ] Add support for message prioritization

## Contributing

This is a portfolio project, but suggestions and feedback are welcome. Feel free to open an issue to discuss potential improvements.

## License

This project is available for review and educational purposes.

## Contact

**Herik Rezende**
- GitHub: [@devherik](https://github.com/devherik)
- LinkedIn: [Connect with me](https://linkedin.com/in/herikrezende)

---

**Note**: This project was built to demonstrate software engineering best practices, Clean Architecture principles, and production-ready Python development. It showcases the ability to design scalable, maintainable systems suitable for real-world applications.
