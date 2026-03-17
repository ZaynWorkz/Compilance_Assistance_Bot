# app/utils/security.py

import hashlib
import hmac
import json
import re
import time
from datetime import datetime, timedelta

class SecurityMiddleware:
    """Security middleware for request validation and protection"""
    
    def __init__(self, secret_key, rate_limiter=None):
        self.secret_key = secret_key
        self.rate_limiter = rate_limiter or RateLimiter(max_requests=100, window_seconds=3600)
        self.allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'csv'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
    def validate_request(self, request_data, signature):
        """Validate request signature"""
        expected = self._generate_signature(request_data)
        return hmac.compare_digest(expected, signature)
    
    def _generate_signature(self, data):
        """Generate HMAC signature for request"""
        message = json.dumps(data, sort_keys=True).encode()
        return hmac.new(
            self.secret_key.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
    
    def sanitize_filename(self, filename):
        """Sanitize uploaded filename"""
        if not filename:
            return "unknown_file"
        
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Remove any non-alphanumeric characters except dots, hyphens and underscores
        filename = re.sub(r'[^\w\-. ]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        
        return filename.strip()
    
    def validate_file(self, filename, file_size, content_type):
        """Validate file for security"""
        # Check file size
        if file_size > self.max_file_size:
            return False, f"File too large. Max size: {self.max_file_size/1024/1024}MB"
        
        # Check extension
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        if ext not in self.allowed_extensions:
            return False, f"File type not allowed. Allowed: {', '.join(self.allowed_extensions)}"
        
        # Basic content type check
        allowed_content_types = ['image', 'pdf', 'sheet', 'csv', 'application']
        if content_type and not any(ct in content_type.lower() for ct in allowed_content_types):
            return False, f"Invalid content type: {content_type}"
        
        return True, "File validation passed"
    
    def sanitize_input(self, text, max_length=1000):
        """Sanitize user input"""
        if not text:
            return ""
        
        # Remove any potentially dangerous characters
        text = re.sub(r'[<>{}()\[\]";]', '', text)
        # Limit length
        return text[:max_length]


class RateLimiter:
    """Rate limiting implementation - no external package needed"""
    
    def __init__(self, max_requests=100, window_seconds=3600):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # Dict[str, list]
    
    def check_rate_limit(self, client_id):
        """
        Check if request is within rate limit
        
        Args:
            client_id: Unique identifier for the client (IP, user ID, etc.)
            
        Returns:
            Tuple of (allowed: bool, info: Dict)
        """
        now = datetime.now()
        
        # Initialize if new client
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Clean old requests outside the window
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < timedelta(seconds=self.window_seconds)
        ]
        
        # Check limit
        current_count = len(self.requests[client_id])
        if current_count >= self.max_requests:
            # Calculate when the oldest request expires
            if self.requests[client_id]:
                oldest = self.requests[client_id][0]
                reset_time = oldest + timedelta(seconds=self.window_seconds)
                reset_in = int((reset_time - now).total_seconds())
            else:
                reset_in = self.window_seconds
            
            return False, {
                'allowed': False,
                'limit': self.max_requests,
                'current': current_count,
                'remaining': 0,
                'reset_in': max(0, reset_in),
                'message': f'Rate limit exceeded. Try again in {reset_in} seconds.'
            }
        
        # Add current request
        self.requests[client_id].append(now)
        
        return True, {
            'allowed': True,
            'limit': self.max_requests,
            'current': current_count + 1,
            'remaining': self.max_requests - (current_count + 1),
            'reset_in': self.window_seconds
        }
    
    def get_client_stats(self, client_id):
        """Get current statistics for a client"""
        if client_id not in self.requests:
            return {
                'client_id': client_id,
                'current_requests': 0,
                'limit': self.max_requests,
                'remaining': self.max_requests
            }
        
        now = datetime.now()
        current_requests = [
            req for req in self.requests[client_id]
            if now - req < timedelta(seconds=self.window_seconds)
        ]
        
        return {
            'client_id': client_id,
            'current_requests': len(current_requests),
            'limit': self.max_requests,
            'remaining': self.max_requests - len(current_requests),
            'window_seconds': self.window_seconds
        }
    
    def reset_client(self, client_id):
        """Reset rate limit for a specific client"""
        if client_id in self.requests:
            del self.requests[client_id]
    
    def reset_all(self):
        """Reset all rate limits"""
        self.requests.clear()