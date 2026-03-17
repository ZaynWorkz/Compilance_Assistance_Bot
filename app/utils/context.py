from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

@dataclass
class WorkflowContext:
    """Context object for workflow state - used by both session and workflow"""
    session_id: str
    current_state: str
    declaration_number: Optional[str] = None
    uploaded_documents: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    validation_results: Optional[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)
    last_activity: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)