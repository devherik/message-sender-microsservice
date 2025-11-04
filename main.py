from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator

from fastapi import FastAPI, Depends
from psycopg2.extensions import connection as PgConnection

from models.interfaces import IDatabaseService
from repositories.postgres_repository import PostgresRepository
from routers import message_router


# The repository is instantiated once and shared across the application.
# This is safe because it holds no per-request state.
db_repository = PostgresRepository()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage startup and shutdown events for the application.
    """
    print("--- Message Sender Microsservice ---")
    print("Connecting to database...")
    # You can add a health check here to ensure the database is reachable on startup
    conn = db_repository.get_connection()
    print(
        "Database connection status:",
        "OK" if db_repository.is_connection_alive(conn) else "Failed",
    )
    db_repository.close_connection(conn)
    yield
    print("--- Shutting down ---")


app = FastAPI(
    title="Message Sender Microsservice",
    description="A microservice for sending messages, built with Clean Architecture.",
    version="0.1.0",
    lifespan=lifespan,
)


# --- Dependency Injection ---
# This is the core of our connection management strategy.
# It adheres to the Dependency Inversion Principle by allowing our endpoints
# to depend on an abstraction (a connection), not a concrete implementation detail.
def get_db_connection() -> Generator[PgConnection, None, None]:
    """
    FastAPI dependency to create and clean up a database connection per request.
    """
    connection = None
    try:
        connection = db_repository.get_connection()
        yield connection
    finally:
        if connection:
            db_repository.close_connection(connection)


def get_db_service() -> IDatabaseService:
    """
    FastAPI dependency that provides the database repository.
    This allows us to easily swap the database implementation in the future.
    """
    return db_repository


@app.get("/")
def read_root(
    db: IDatabaseService = Depends(get_db_service),
    conn: PgConnection = Depends(get_db_connection),
):
    """
    Root endpoint to check service and database status.
    """
    return {
        "service": "message-sender-microsservice",
        "status": "ok",
        "database_info": db.get_connection_info(conn),
    }


app.include_router(message_router.router, prefix="/api", tags=["Messages"])


# To run this application:
# uvicorn main:app --reload
