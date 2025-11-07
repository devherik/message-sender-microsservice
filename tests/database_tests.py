from core.dependencies import db_repository

def postgres_db_status() -> bool:
    """
    Provides system information.
    """
    connection = None
    try:
        connection = db_repository.get_connection()
        is_alive = db_repository.is_connection_alive(connection)
        return is_alive
    finally:
        if connection:
            db_repository.close_connection(connection)