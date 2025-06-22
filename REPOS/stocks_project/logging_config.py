#!/usr/bin/env python3
"""
Enhanced Logging Configuration for Stocks Project
Production-grade logging system for debugging during prototype phase
"""

import logging
import logging.handlers
import os
import json
import uuid
from datetime import datetime
from functools import wraps

# Flask imports - conditional for standalone use
try:
    from flask import request, g
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    # Mock objects for standalone use
    class MockRequest:
        method = 'GET'
        path = '/test'
        args = {}
        def get_json(self): return None
        @property
        def is_json(self): return False
        @property
        def headers(self): return {}
    
    class MockG:
        request_id = 'test-req'
    
    request = MockRequest()
    g = MockG()


class RequestIDFilter(logging.Filter):
    """Add request ID to log records for request tracing"""
    
    def filter(self, record):
        if hasattr(g, 'request_id'):
            record.request_id = g.request_id
        else:
            record.request_id = 'no-request'
        return True


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easier parsing and monitoring"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'request_id': getattr(record, 'request_id', 'no-request'),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data['extra_data'] = record.extra_data
            
        return json.dumps(log_data)


def setup_logging(app_name='stocks_app', log_level='INFO'):
    """
    Setup comprehensive logging system
    
    Args:
        app_name: Name of the application
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(RequestIDFilter())
    
    # File handler with rotation for production
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, f'{app_name}.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    file_handler.addFilter(RequestIDFilter())
    
    # Error-only file handler
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, f'{app_name}_errors.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    error_handler.addFilter(RequestIDFilter())
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger


def log_api_call(logger):
    """Decorator to log API calls with request/response details"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate request ID
            g.request_id = str(uuid.uuid4())[:8]
            
            start_time = datetime.utcnow()
            
            # Log request
            logger.info(
                f"API Request: {request.method} {request.path}",
                extra={'extra_data': {
                    'method': request.method,
                    'path': request.path,
                    'args': dict(request.args),
                    'json_data': request.get_json() if request.is_json else None,
                    'user_agent': request.headers.get('User-Agent', 'Unknown')
                }}
            )
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Calculate response time
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                # Log successful response
                logger.info(
                    f"API Response: {request.method} {request.path} - {response_time:.2f}ms",
                    extra={'extra_data': {
                        'response_time_ms': response_time,
                        'status': 'success'
                    }}
                )
                
                return result
                
            except Exception as e:
                # Calculate response time for error case
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                # Log error with context
                logger.error(
                    f"API Error: {request.method} {request.path} - {str(e)}",
                    exc_info=True,
                    extra={'extra_data': {
                        'response_time_ms': response_time,
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'request_data': {
                            'args': dict(request.args),
                            'json': request.get_json() if request.is_json else None
                        }
                    }}
                )
                raise
                
        return wrapper
    return decorator


def log_analysis_phase(logger, phase_name):
    """Decorator to log analysis phases with timing and error handling"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            
            logger.info(
                f"Analysis Phase Started: {phase_name}",
                extra={'extra_data': {'phase': phase_name, 'action': 'start'}}
            )
            
            try:
                result = func(*args, **kwargs)
                
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(
                    f"Analysis Phase Completed: {phase_name} - {duration:.2f}s",
                    extra={'extra_data': {
                        'phase': phase_name,
                        'action': 'complete',
                        'duration_seconds': duration
                    }}
                )
                
                return result
                
            except Exception as e:
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                logger.error(
                    f"Analysis Phase Failed: {phase_name} - {str(e)}",
                    exc_info=True,
                    extra={'extra_data': {
                        'phase': phase_name,
                        'action': 'failed',
                        'duration_seconds': duration,
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    }}
                )
                raise
                
        return wrapper
    return decorator


def log_file_operation(logger, operation_type):
    """Decorator to log file operations with error handling"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract filename from args/kwargs
            filename = 'unknown'
            if args:
                filename = str(args[0])
            elif 'filename' in kwargs:
                filename = kwargs['filename']
            elif 'file_path' in kwargs:
                filename = kwargs['file_path']
            
            logger.debug(
                f"File Operation: {operation_type} - {filename}",
                extra={'extra_data': {
                    'operation': operation_type,
                    'filename': filename,
                    'action': 'start'
                }}
            )
            
            try:
                result = func(*args, **kwargs)
                
                logger.debug(
                    f"File Operation Success: {operation_type} - {filename}",
                    extra={'extra_data': {
                        'operation': operation_type,
                        'filename': filename,
                        'action': 'success'
                    }}
                )
                
                return result
                
            except Exception as e:
                logger.error(
                    f"File Operation Failed: {operation_type} - {filename} - {str(e)}",
                    exc_info=True,
                    extra={'extra_data': {
                        'operation': operation_type,
                        'filename': filename,
                        'action': 'failed',
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    }}
                )
                raise
                
        return wrapper
    return decorator


# Create default logger instance
main_logger = setup_logging('stocks_app', 'INFO')