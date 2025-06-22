#!/usr/bin/env python3
"""
Input validation module for Penny Stock Analysis API
Provides robust validation for all API endpoints
"""

import re
import html
from typing import Dict, Any, Optional, List, Union
from flask import jsonify
from logging_config import main_logger

# Validation constants
VALID_CATEGORIES = ['under-5', '5-to-10', '10-to-20']
TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}$')  # 1-5 uppercase letters
MAX_TICKER_LENGTH = 5
MIN_TICKER_LENGTH = 1

class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class APIValidator:
    """Centralized API input validation"""
    
    @staticmethod
    def validate_ticker(ticker: str) -> str:
        """
        Validate stock ticker format with XSS protection
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Validated ticker in uppercase
            
        Raises:
            ValidationError: If ticker is invalid or contains malicious content
        """
        if not ticker:
            raise ValidationError("Ticker symbol is required")
        
        if not isinstance(ticker, str):
            raise ValidationError("Ticker must be a string")
        
        # Check for potential XSS patterns before any processing
        xss_patterns = [
            r'<\s*script',      # <script> tags
            r'<\s*iframe',      # <iframe> tags  
            r'<\s*object',      # <object> tags
            r'<\s*embed',       # <embed> tags
            r'<\s*link',        # <link> tags
            r'<\s*meta',        # <meta> tags
            r'javascript:',     # javascript: protocol
            r'data:',           # data: protocol
            r'vbscript:',       # vbscript: protocol
            r'on\w+\s*=',       # event handlers (onclick, onload, etc.)
            r'<\s*\w+[^>]*>',   # any HTML tags
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, ticker, re.IGNORECASE):
                main_logger.warning(f"XSS attempt detected in ticker: {ticker}")
                raise ValidationError("Invalid ticker format: Contains prohibited characters")
        
        # Clean and uppercase
        ticker = ticker.strip().upper()
        
        # Additional character filtering - only allow alphanumeric and basic punctuation
        if re.search(r'[<>"\';\\&%#]', ticker):
            raise ValidationError("Ticker contains invalid characters")
        
        if len(ticker) < MIN_TICKER_LENGTH or len(ticker) > MAX_TICKER_LENGTH:
            raise ValidationError(f"Ticker must be {MIN_TICKER_LENGTH}-{MAX_TICKER_LENGTH} characters long")
        
        if not TICKER_PATTERN.match(ticker):
            raise ValidationError("Ticker must contain only uppercase letters")
        
        return ticker
    
    @staticmethod
    def validate_category(category: str) -> str:
        """
        Validate category name
        
        Args:
            category: Category name
            
        Returns:
            Validated category name
            
        Raises:
            ValidationError: If category is invalid
        """
        if not category:
            raise ValidationError("Category is required")
        
        if not isinstance(category, str):
            raise ValidationError("Category must be a string")
        
        # Clean input
        category = category.strip().lower()
        
        if category not in VALID_CATEGORIES:
            raise ValidationError(f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}")
        
        return category
    
    @staticmethod
    def validate_json_content_type(request) -> None:
        """
        Validate that request has proper JSON content type
        
        Args:
            request: Flask request object
            
        Raises:
            ValidationError: If content type is invalid
        """
        if not request.is_json:
            raise ValidationError("Request must have Content-Type: application/json", 415)
    
    @staticmethod
    def validate_request_size(request, max_size: int = 1024) -> None:
        """
        Validate request body size
        
        Args:
            request: Flask request object
            max_size: Maximum allowed size in bytes
            
        Raises:
            ValidationError: If request is too large
        """
        if request.content_length and request.content_length > max_size:
            raise ValidationError(f"Request body too large. Maximum {max_size} bytes allowed", 413)
    
    @staticmethod
    def validate_analysis_request(request) -> Dict[str, Any]:
        """
        Validate analysis start request
        
        Args:
            request: Flask request object
            
        Returns:
            Validated request data
            
        Raises:
            ValidationError: If request is invalid
        """
        # Validate content type
        APIValidator.validate_json_content_type(request)
        
        # Validate request size
        APIValidator.validate_request_size(request)
        
        # Get JSON data
        try:
            data = request.get_json(force=True)
        except Exception as e:
            raise ValidationError(f"Invalid JSON: {str(e)}")
        
        # Ensure data is a dictionary
        if not isinstance(data, dict):
            raise ValidationError("Request body must be a JSON object")
        
        # Analysis requests should be empty or contain minimal data
        allowed_keys = {'force_restart', 'analysis_type'}
        extra_keys = set(data.keys()) - allowed_keys
        if extra_keys:
            raise ValidationError(f"Unexpected fields: {', '.join(extra_keys)}")
        
        return data
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 100) -> str:
        """
        Sanitize string input for security with comprehensive XSS protection
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
            
        Raises:
            ValidationError: If string is invalid or contains malicious content
        """
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")
        
        # Strip whitespace
        value = value.strip()
        
        if len(value) > max_length:
            raise ValidationError(f"String too long. Maximum {max_length} characters allowed")
        
        # Check for XSS patterns
        xss_patterns = [
            r'<\s*script',      # <script> tags
            r'<\s*iframe',      # <iframe> tags  
            r'<\s*object',      # <object> tags
            r'<\s*embed',       # <embed> tags
            r'<\s*form',        # <form> tags
            r'<\s*input',       # <input> tags
            r'javascript:',     # javascript: protocol
            r'data:text/html',  # data: protocol with HTML
            r'vbscript:',       # vbscript: protocol
            r'on\w+\s*=',       # event handlers
            r'expression\s*\(',  # CSS expressions
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                main_logger.warning(f"XSS attempt detected in string: {value[:50]}...")
                raise ValidationError("Invalid input: Contains prohibited content")
        
        # HTML escape the entire value for safety
        value = html.escape(value, quote=True)
        
        # Additional filtering for dangerous characters
        dangerous_chars = r'[<>"\';\\&%#]'
        if re.search(dangerous_chars, value):
            # Remove dangerous characters after HTML escaping
            value = re.sub(dangerous_chars, '', value)
        
        return value

def handle_validation_error(error: ValidationError) -> tuple:
    """
    Handle validation errors and return appropriate JSON response
    
    Args:
        error: ValidationError instance
        
    Returns:
        Tuple of (response, status_code)
    """
    main_logger.warning(f"Validation error: {error.message}")
    return jsonify({
        'status': 'error',
        'message': error.message,
        'error_type': 'validation_error'
    }), error.status_code

def validation_required(validation_func):
    """
    Decorator for API endpoints that require validation
    
    Args:
        validation_func: Function to validate the request
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                # Run validation
                validation_func(*args, **kwargs)
                # If validation passes, call the original function
                return f(*args, **kwargs)
            except ValidationError as e:
                return handle_validation_error(e)
            except Exception as e:
                # Handle unexpected errors
                main_logger.error(f"Internal validation error: {str(e)}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': 'Internal validation error',
                    'error_type': 'server_error'
                }), 500
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator