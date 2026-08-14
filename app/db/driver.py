import logging
from typing import Callable, Any, Optional
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, Neo4jError
from app.config import settings

logger = logging.getLogger("offboardguard.db")

_driver_instance: Optional[Driver] = None
_db_connected: bool = False

def get_driver() -> Optional[Driver]:
    global _driver_instance
    if _driver_instance is None:
        try:
            _driver_instance = GraphDatabase.driver(
                settings.COGNO_URI,
                auth=(settings.COGNO_USER, settings.COGNO_PASSWORD)
            )
        except Exception as e:
            logger.error(f"Failed to create Neo4j driver: {e}")
            _driver_instance = None
    return _driver_instance

def is_db_connected() -> bool:
    global _db_connected
    return _db_connected

def check_connectivity() -> bool:
    global _db_connected
    try:
        driver = get_driver()
        if driver is None:
            _db_connected = False
            return False
        driver.verify_connectivity()
        _db_connected = True
        logger.info("Successfully connected to CognoDB graph database.")
        return True
    except (ServiceUnavailable, Neo4jError, Exception) as e:
        _db_connected = False
        logger.warning(f"CognoDB connectivity check failed: {e}")
        return False

def close_driver():
    global _driver_instance, _db_connected
    if _driver_instance is not None:
        try:
            _driver_instance.close()
        except Exception as e:
            logger.error(f"Error closing Neo4j driver: {e}")
        _driver_instance = None
    _db_connected = False

def execute_read(transaction_function: Callable, **kwargs) -> Any:
    """
    Execute a read query inside a managed transaction session.
    If CognoDB is unreachable, passes tx=None to trigger local fallback evaluation.
    """
    global _db_connected
    if not _db_connected:
        return transaction_function(None, **kwargs)

    try:
        driver = get_driver()
        with driver.session() as session:
            return session.execute_read(transaction_function, **kwargs)
    except (ServiceUnavailable, Neo4jError, Exception) as e:
        logger.warning(f"Database read query failed ({e}). Falling back to local offline evaluation.")
        _db_connected = False
        return transaction_function(None, **kwargs)

def execute_write(transaction_function: Callable, **kwargs) -> Any:
    """
    Execute a write query inside a managed transaction session.
    """
    global _db_connected
    if not _db_connected:
        return transaction_function(None, **kwargs)

    try:
        driver = get_driver()
        with driver.session() as session:
            return session.execute_write(transaction_function, **kwargs)
    except (ServiceUnavailable, Neo4jError, Exception) as e:
        logger.warning(f"Database write query failed ({e}).")
        _db_connected = False
        return transaction_function(None, **kwargs)
