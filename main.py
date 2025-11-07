from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, Request
from psycopg2.extensions import connection as PgConnection

from core.dependencies import get_db_connection, get_db_service, db_repository
from models.interfaces import IDatabaseService
from routers import message_router
from helpers.logging_helper import logger
from middlewares.correlation_id_mw import correlation_id_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage startup and shutdown events for the application.
    """
    logger.info("--- Message Sender Microsservice ---")
    logger.info("Connecting to database...")
    # You can add a health check here to ensure the database is reachable on startup
    try:
        conn = db_repository.get_connection()
        logger.info(
            f"Database connection status: {'OK' if db_repository.is_connection_alive(conn) else 'Failed'}"
        )
        db_repository.close_connection(conn)
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
    yield
    logger.info("--- Shutting down ---")


app = FastAPI(
    title="Message Sender Microsservice",
    description="A microservice for sending messages, built with Clean Architecture.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Health"], response_model=dict)
def read_root(
    request: Request,
    db: IDatabaseService = Depends(get_db_service),
    conn: PgConnection = Depends(get_db_connection),
):
    """
    Root endpoint to check service and database status.
    """
    logger.info("Root endpoint called.", correlation_id=request.state.correlation_id)
    return {
        "service": "message-sender-microsservice",
        "status": "ok",
        "database_info": db.get_connection_info(conn),
    }


app.include_router(message_router.router, prefix="/api", tags=["Messages"])

app.middleware("http")(correlation_id_middleware)


# To run this application:
# uvicorn main:app --reload
