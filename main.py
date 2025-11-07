from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, Request
from psycopg2.extensions import connection as PgConnection

from core.dependencies import get_db_connection, get_db_service
from models.interfaces import IDatabaseService
from models.models import ResponseModel, SystemInfo
from tests.database_tests import postgres_db_status
from routers import message_router
from helpers.logging_helper import logger
from middlewares.correlation_id_mw import correlation_id_middleware

async def startup_event(app: FastAPI):
    logger.info(f"--- Message Sender Microsservice | version {app.version} ---")
    sys_status: SystemInfo = SystemInfo(
        os="Linux",
        python_version="3.12",
        service_uptime="72 hours",
        all_dependencies_working=True,
        system_tests={"test_db_connection": postgres_db_status()},
    )
    logger.info(f"System Status on Startup: {sys_status.system_tests}")

async def shutdown_event(app: FastAPI):
    logger.info(f"--- Shutting down | version {app.version} ---")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage startup and shutdown events for the application.
    """
    try:
        await startup_event(app)
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
    finally:
        yield
        await shutdown_event(app)


app = FastAPI(
    title="Message Sender Microsservice",
    description="A microservice for sending messages, built with Clean Architecture.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Health"], response_model=ResponseModel)
def read_root(
    request: Request,
    db: IDatabaseService = Depends(get_db_service),
    conn: PgConnection = Depends(get_db_connection),
):
    """
    Root endpoint to check service and database status.
    """
    logger.info("Root endpoint called.", correlation_id=request.state.correlation_id)
    return ResponseModel(
        success=True,
        message="Service is running",
        data={
            "service": "message-sender-microsservice",
            "status": "ok",
            "database_info": db.get_connection_info(conn),
        }
    )

app.include_router(message_router.router, prefix="/api", tags=["Messages"])

app.middleware("http")(correlation_id_middleware)


# To run this application:
# uvicorn main:app --reload
