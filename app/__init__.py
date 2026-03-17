# app/workflow/__init__.py (UPDATE THIS)

# Don't import orchestrator here to avoid circular imports
from app.workflow.state_machine import StateMachine, WorkflowState, DocumentType

__all__ = ['StateMachine', 'WorkflowState', 'DocumentType']
