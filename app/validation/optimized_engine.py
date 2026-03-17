# app/validation/optimized_engine.py

from .engine import ValidationEngine
from ..utils.cache import cached

class OptimizedValidationEngine(ValidationEngine):
    """Validation engine with caching for performance"""
    
    @cached(ttl=60)  # Cache results for 1 minute
    def validate_all_documents(self, declaration_number, uploaded_documents):
        """
        Validate all documents with caching
        Results are cached for 60 seconds to avoid repeated validation
        """
        return super().validate_all_documents(declaration_number, uploaded_documents)