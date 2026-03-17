# app/utils/exceptions.py

"""
Custom exceptions for the Compliance Assistant
"""

from enum import Enum

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkflowError(Exception):
    """Base exception for workflow errors"""
    
    def __init__(self, message, severity=ErrorSeverity.MEDIUM, context=None, user_message=None):
        self.message = message
        self.severity = severity
        self.context = context or {}
        self.user_message = user_message or "An error occurred. Please try again."
        super().__init__(self.message)


class ValidationError(WorkflowError):
    """Exception for validation failures"""
    
    def __init__(self, message, field=None, expected=None, received=None, **kwargs):
        context = {
            'field': field,
            'expected': expected,
            'received': received
        }
        user_message = f"Validation failed for {field}."
        if expected and received:
            user_message = f"Validation failed for {field}. Expected {expected}, received {received}"
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            user_message=user_message
        )


class DocumentProcessingError(WorkflowError):
    """Exception for document processing failures"""
    
    def __init__(self, message, document_type=None, filename=None, **kwargs):
        context = {
            'document_type': document_type,
            'filename': filename
        }
        user_message = f"Error processing {document_type or 'document'}"
        if filename:
            user_message += f": {filename}"
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            context=context,
            user_message=user_message
        )


class StateTransitionError(WorkflowError):
    """Exception for invalid state transitions"""
    
    def __init__(self, message, from_state=None, to_state=None, **kwargs):
        context = {
            'from_state': from_state,
            'to_state': to_state
        }
        user_message = f"Cannot transition from {from_state or 'unknown'} to {to_state or 'unknown'}"
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            context=context,
            user_message=user_message
        )


class SessionError(WorkflowError):
    """Exception for session-related errors"""
    
    def __init__(self, message, session_id=None, **kwargs):
        context = {
            'session_id': session_id
        }
        user_message = "Session error occurred. Please restart the session."
        super().__init__(
            message=message,
            severity=ErrorSeverity.CRITICAL,
            context=context,
            user_message=user_message
        )


class FileValidationError(WorkflowError):
    """Exception for file validation failures"""
    
    def __init__(self, message, filename=None, file_size=None, **kwargs):
        context = {
            'filename': filename,
            'file_size': file_size
        }
        user_message = f"File validation failed: {message}"
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            user_message=user_message
        )


class DatabaseError(WorkflowError):
    """Exception for database operations"""
    
    def __init__(self, message, operation=None, **kwargs):
        context = {
            'operation': operation
        }
        user_message = "Database error occurred. Please try again."
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            context=context,
            user_message=user_message
        )


class ConfigurationError(WorkflowError):
    """Exception for configuration errors"""
    
    def __init__(self, message, config_key=None, **kwargs):
        context = {
            'config_key': config_key
        }
        user_message = f"Configuration error: {message}"
        super().__init__(
            message=message,
            severity=ErrorSeverity.CRITICAL,
            context=context,
            user_message=user_message
        )