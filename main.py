from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, Request
from psycopg2.extensions import connection as PgConnection

from core.dependencies import get_db_repository
from core.settings import settings
from repositories.database_interfaces import IDatabaseRepository
from models.models import SystemInfo
from routers import message_router, test_router
from routers import data_ingestion_router, routing_rules_router, statistics_router
from routers.schemas import ResponseModel
from middlewares.correlation_id_mw import correlation_id_middleware
from tests.database_tests import postgres_db_status
from helpers.logging_helper import logger
from helpers.uptime_helper import uptime_helper


async def startup_event(app: FastAPI):
    logger.info(
        f"--- Message Sender Microsservice | version {app.version} |  {'Development' if settings.environment == 'development' else 'Production'} ---"
    )
    try:
        sys_status: SystemInfo = SystemInfo(
            os="Linux",
            python_version="3.12",
            service_uptime=uptime_helper.get_uptime(),
            all_dependencies_working=True,
            system_tests={"test_db_connection": postgres_db_status()},
        )
    except Exception as e:
        logger.error(f"Error during startup: {e}")
    logger.info(
        f"System Status on Startup {'Development' if settings.environment == 'development' else 'Production'}: {sys_status.system_tests}"
    )


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
    title="Versatile Data Ingestion Platform",
    description="A microservice for ingesting data from N applications, routing, persisting, and providing analytics. Built with Clean Architecture.",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Health"], response_model=ResponseModel)
def read_root(request: Request, db: IDatabaseRepository = Depends(get_db_repository)):
    """
    Root endpoint to check service and database status.
    """
    logger.info("Root endpoint called.")
    conn: PgConnection = db.get_connection()
    return ResponseModel(
        success=True,
        message="Service is running",
        data={
            "service": "message-sender-microsservice",
            "status": "ok",
            "uptime": uptime_helper.get_uptime(),
            "is_db_connected": db.is_connection_alive(conn),
        },
    )


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint to monitor service uptime.
    """
    return {"status": "ok", "uptime": uptime_helper.get_uptime()}


# Legacy message-sending endpoints (backward compatible)
app.include_router(message_router.router, prefix="/api", tags=["Messages"])
app.include_router(test_router.router, prefix="/api", tags=["Tests"])

# Data Ingestion Platform endpoints
app.include_router(data_ingestion_router.router, prefix="/api", tags=["Data Ingestion"])
app.include_router(routing_rules_router.router, prefix="/api", tags=["Routing Rules"])
app.include_router(statistics_router.router, prefix="/api", tags=["Statistics"])

app.middleware("http")(correlation_id_middleware)


# To run this application:
# uvicorn main:app --reload
