# app/utils/error_handler.py

import logging
import traceback
import time
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling with recovery strategies"""
    
    def __init__(self, session_manager=None):
        self.session_manager = session_manager
        self.error_count = 0
        self.max_errors = 5
        self.error_history = []
        
    def handle_exception(self, error, context=None):
        """
        Handle exceptions and return user-friendly message
        """
        self.error_count += 1
        error_id = self._generate_error_id()
        
        # Store error in history
        self.error_history.append({
            'error_id': error_id,
            'error_type': error.__class__.__name__,
            'message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        })
        
        # Keep only last 10 errors
        if len(self.error_history) > 10:
            self.error_history = self.error_history[-10:]
        
        # Log full error details
        logger.error(
            f"Error {error_id}: {str(error)}",
            exc_info=True,
            extra={
                'error_id': error_id,
                'error_type': error.__class__.__name__,
                'context': context
            }
        )
        
        # Check if error threshold exceeded
        if self.error_count >= self.max_errors:
            self._handle_critical_failure()
            return "System encountered too many errors. Please restart the session."
        
        # Return appropriate user message
        error_name = error.__class__.__name__
        if 'Validation' in error_name:
            return f"Validation error: {str(error)}"
        elif 'Document' in error_name:
            return f"Document processing error: {str(error)}"
        elif 'Session' in error_name:
            return "Session error. Please restart the session."
        else:
            return f"An unexpected error occurred (ID: {error_id}). Please try again."
    
    def _generate_error_id(self):
        """Generate unique error ID for tracking"""
        import uuid
        return f"ERR-{uuid.uuid4().hex[:8].upper()}"
    
    def _handle_critical_failure(self):
        """Handle critical failure by resetting session"""
        logger.critical("Critical error threshold exceeded. Resetting session.")
        if self.session_manager and hasattr(self.session_manager, 'reset_session'):
            self.session_manager.reset_session()
        self.error_count = 0
    
    def get_error_summary(self):
        """Get summary of errors for debugging"""
        return {
            'total_errors': self.error_count,
            'recent_errors': self.error_history[-5:],
            'max_errors': self.max_errors
        }


def with_error_handling(func):
    """Decorator for error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            return f"An error occurred in {func.__name__}. Please try again."
    return wrapper


def retry_on_failure(max_retries=3, delay=1):
    """Decorator for retrying failed operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
            
            # All retries failed
            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_error
        return wrapper
    return decorator