# app/workflow/orchestrator.py (UPDATE THIS)

import logging
from typing import Dict, Any

# Import SessionStateManager directly - this is fine
from app.session.state_manager import SessionStateManager
from ..validation.engine import ValidationEngine
from ..conversation.router import ConversationRouter
from app.workflow.state_machine import WorkflowState

logger = logging.getLogger(__name__)

class WorkflowOrchestrator:
    """Orchestrates the entire workflow"""
    
    def __init__(self, 
                 session_manager: SessionStateManager,
                 validation_engine: ValidationEngine,
                 conversation_router: ConversationRouter):
        self.session_manager = session_manager
        self.validation_engine = validation_engine
        self.conversation_router = conversation_router
    
    # ... rest of methods