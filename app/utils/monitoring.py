# app/utils/monitoring.py

import time
from functools import wraps
from datetime import datetime

# Simple metrics storage
_metrics = {
    'workflow_starts': 0,
    'workflow_completions': 0,
    'workflow_errors': {},
    'document_uploads': {},
    'validation_results': {'success': 0, 'failure': 0},
    'processing_times': {},
    'active_sessions': 0,
    'start_time': datetime.now()
}

def monitor_operation(operation_name):
    """Decorator to monitor operation duration"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if operation_name not in _metrics['processing_times']:
                    _metrics['processing_times'][operation_name] = []
                _metrics['processing_times'][operation_name].append(duration)
                # Keep only last 100 timings
                if len(_metrics['processing_times'][operation_name]) > 100:
                    _metrics['processing_times'][operation_name] = _metrics['processing_times'][operation_name][-100:]
        return wrapper
    return decorator

def track_workflow_start():
    """Track workflow start"""
    global _metrics
    _metrics['workflow_starts'] += 1
    _metrics['active_sessions'] += 1

def track_workflow_completion():
    """Track workflow completion"""
    global _metrics
    _metrics['workflow_completions'] += 1
    _metrics['active_sessions'] = max(0, _metrics['active_sessions'] - 1)

def track_workflow_error(error_type):
    """Track workflow error"""
    global _metrics
    if error_type not in _metrics['workflow_errors']:
        _metrics['workflow_errors'][error_type] = 0
    _metrics['workflow_errors'][error_type] += 1

def track_document_upload(document_type):
    """Track document upload"""
    global _metrics
    if document_type not in _metrics['document_uploads']:
        _metrics['document_uploads'][document_type] = 0
    _metrics['document_uploads'][document_type] += 1

def track_validation(status):
    """Track validation result"""
    global _metrics
    if status in _metrics['validation_results']:
        _metrics['validation_results'][status] += 1

def get_metrics():
    """Get all metrics"""
    global _metrics
    return {
        'uptime_seconds': (datetime.now() - _metrics['start_time']).total_seconds(),
        **_metrics
    }   