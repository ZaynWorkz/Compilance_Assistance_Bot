# app/session/attempt_tracker.py (VERIFY THIS)

class AttemptTracker:
    """Track upload attempts per document with 3-attempt rule"""
    
    def __init__(self, max_attempts=3):
        self.max_attempts = max_attempts
        self.attempts = {}  # Format: {doc_type: {'total': 0, 'failed': 0}}
        self.failed_documents = []
        self.session_aborted = False
    
    def register_attempt(self, document_type, success=True):
        """
        Register an upload attempt
        Returns: (can_continue, message)
        """
        if document_type not in self.attempts:
            self.attempts[document_type] = {'total': 0, 'failed': 0}
        
        self.attempts[document_type]['total'] += 1
        
        if not success:
            self.attempts[document_type]['failed'] += 1
            
            # Check if max attempts exceeded
            if self.attempts[document_type]['failed'] >= self.max_attempts:
                self.failed_documents.append(document_type)
                self.session_aborted = True
                return False, "MAX_ATTEMPTS_EXCEEDED"
        
        attempts_left = self.max_attempts - self.attempts[document_type]['failed']
        return True, f"{attempts_left} {'attempt' if attempts_left == 1 else 'attempts'} left"
    
    def get_attempts(self, document_type):
        """Get attempt count for a document"""
        if document_type in self.attempts:
            return {
                'total': self.attempts[document_type]['total'],
                'failed': self.attempts[document_type]['failed'],
                'remaining': self.max_attempts - self.attempts[document_type]['failed']
            }
        # Return default values if document_type not found
        return {
            'total': 0,
            'failed': 0,
            'remaining': self.max_attempts
        }
    
    def can_continue(self):
        """Check if session can continue"""
        return not self.session_aborted
    
    def reset(self):
        """Reset tracker for new session"""
        self.attempts = {}
        self.failed_documents = []
        self.session_aborted = False