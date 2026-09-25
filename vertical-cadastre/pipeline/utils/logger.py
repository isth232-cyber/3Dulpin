import logging
import os
import time

def get_logger(name, log_file="reports/system.log", level=logging.INFO):
    """
    Returns a logger that writes to both console and a log file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
    return logger

def log_operation(logger, operation_name):
    """
    A decorator for logging operations with duration and success/failure.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"Starting operation: {operation_name}")
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Successfully completed: {operation_name} in {duration:.4f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Failed operation: {operation_name} after {duration:.4f}s - Error: {str(e)}")
                raise
        return wrapper
    return decorator
