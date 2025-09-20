import logging
import sys
from functools import wraps
from typing import Any
from src.core.config import settings
import os

os.makedirs(settings.storage.log_file.parent, exist_ok=True)

def get_logger(name:str = "fake_certificate_detection") -> logging.Logger:
    """Get a Logger instance"""

    logger = logging.getLogger(name)

    if not logger.handlers:
        # basic configuration
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        file_handler = logging.FileHandler(settings.storage.log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.addHandler(file_handler)

        logger.setLevel(logging.INFO)
    
    return logger


def log_api_call(api_name: str):
    """Simple decorator to log API calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger = get_logger()
            logger.debug(f"API call to {api_name} started")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"API call to {api_name} Completed")
                return result
            except Exception as e:
                logger.error(f"API call to {api_name} Failed : {e}")
                raise
        return wrapper
    return decorator

class LogContext:
    """Simple context manager for Logging"""

    def __init__(self, operation:str, **context):
        self.operation = operation
        self.context = context
        self.logger = get_logger()
    
    def __enter__(self):
        self.logger.debug(f"Starting {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.debug(f"Completed {self.operation}")
        else:
            self.logger.error(f"Failed {self.operation}: {exc_val}")


# Placeholder functions for compatibility
def audit_log(event: str, **kwargs):
    logger = get_logger()
    logger.info(f"AUDIT: {event}")


def performance_log(operation: str, duration: float, **kwargs):
    logger = get_logger()
    logger.info(f"PERF: {operation} took {duration:.2f}s") 