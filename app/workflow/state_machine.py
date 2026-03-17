# app/workflow/state_machine.py

from enum import Enum, auto
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

class StateMachine:
    """Manages workflow state transitions"""
    
    def __init__(self):
        self._transitions = self._define_transitions()
        self._mandatory_documents = [
            DocumentType.DECLARATION,
            DocumentType.INVOICE,
            DocumentType.PACKING_LIST,
            DocumentType.BOL_AWS,
            DocumentType.COUNTRY_OF_ORIGIN,
            DocumentType.DELIVERY_ORDER
        ]
        
class WorkflowState(Enum):
    """Enumeration of all possible workflow states"""
    INITIAL = auto()
    AWAITING_DECLARATION_NUMBER = auto()
    DECLARATION_NUMBER_RECEIVED = auto()
    AWAITING_DOCUMENT = auto()
    DOCUMENT_RECEIVED = auto()
    VALIDATING = auto()
    VALIDATION_FAILED = auto()
    VALIDATION_SUCCESS = auto()
    COMPLETED = auto()
    ERROR = auto()
    RESTARTING = auto()

class DocumentType(Enum):
    """Document types in the workflow"""
    DECLARATION = "declaration"
    INVOICE = "invoice"
    PACKING_LIST = "packing_list"
    BOL_AWS = "bol_aws"
    COUNTRY_OF_ORIGIN = "country_of_origin"
    DELIVERY_ORDER = "delivery_order"
    OTHERS = "others"

@dataclass
class WorkflowContext:
    """Context object for workflow state"""
    session_id: str
    current_state: WorkflowState
    declaration_number: Optional[str] = None
    uploaded_documents: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    validation_results: Optional[Dict[str, Any]] = None
    errors: list = field(default_factory=list)
    last_activity: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class StateMachine:
    """Manages workflow state transitions with validation"""
    
    def __init__(self):
        self._transitions = self._define_transitions()
        self._mandatory_documents = [
            DocumentType.DECLARATION,
            DocumentType.INVOICE,
            DocumentType.PACKING_LIST,
            DocumentType.BOL_AWS,
            DocumentType.COUNTRY_OF_ORIGIN,
            DocumentType.DELIVERY_ORDER
        ]
    
    def _define_transitions(self) -> Dict[WorkflowState, Dict[str, Any]]:
        """Define valid state transitions and their rules"""
        return {
            WorkflowState.INITIAL: {
                'next': WorkflowState.AWAITING_DECLARATION_NUMBER,
                'action': 'initialize_session',
                'requires': []
            },
            WorkflowState.AWAITING_DECLARATION_NUMBER: {
                'next': WorkflowState.DECLARATION_NUMBER_RECEIVED,
                'action': 'process_declaration_number',
                'requires': ['declaration_number']
            },
            WorkflowState.DECLARATION_NUMBER_RECEIVED: {
                'next': WorkflowState.AWAITING_DOCUMENT,
                'action': 'prepare_document_upload',
                'requires': []
            },
            WorkflowState.AWAITING_DOCUMENT: {
                'next': WorkflowState.DOCUMENT_RECEIVED,
                'action': 'process_document',
                'requires': ['document']
            },
            WorkflowState.DOCUMENT_RECEIVED: {
                'next': WorkflowState.VALIDATING,
                'action': 'validate_documents',
                'requires': []
            },
            WorkflowState.VALIDATING: {
                'success': WorkflowState.VALIDATION_SUCCESS,
                'failure': WorkflowState.VALIDATION_FAILED,
                'action': 'run_validation',
                'requires': ['all_mandatory_documents']
            },
            WorkflowState.VALIDATION_FAILED: {
                'next': WorkflowState.AWAITING_DOCUMENT,
                'action': 'handle_validation_failure',
                'requires': ['mismatch_info']
            },
            WorkflowState.VALIDATION_SUCCESS: {
                'next': WorkflowState.COMPLETED,
                'action': 'complete_workflow',
                'requires': []
            }
        }
    
    def can_transition(self, from_state: WorkflowState, to_state: WorkflowState, context: WorkflowContext) -> bool:
        """Validate if transition is allowed"""
        if from_state not in self._transitions:
            return False
        
        transition_rules = self._transitions[from_state]
        
        # Check if it's a valid next state
        if 'next' in transition_rules and transition_rules['next'] == to_state:
            return self._validate_requirements(transition_rules.get('requires', []), context)
        
        # Check for conditional transitions
        if 'success' in transition_rules and to_state == transition_rules['success']:
            return self._validate_requirements(transition_rules.get('requires', []), context)
        
        if 'failure' in transition_rules and to_state == transition_rules['failure']:
            return self._validate_requirements(transition_rules.get('requires', []), context)
        
        return False
    
    def _validate_requirements(self, requirements: list, context: WorkflowContext) -> bool:
        """Validate that all requirements are met"""
        for req in requirements:
            if req == 'declaration_number' and not context.declaration_number:
                return False
            elif req == 'document' and not context.uploaded_documents:
                return False
            elif req == 'all_mandatory_documents':
                if not self._all_mandatory_documents_uploaded(context):
                    return False
            elif req == 'mismatch_info' and not context.validation_results:
                return False
        return True
    
    def _all_mandatory_documents_uploaded(self, context: WorkflowContext) -> bool:
        """Check if all mandatory documents are uploaded"""
        uploaded_types = {doc['document_type'] for doc in context.uploaded_documents.values()}
        return all(doc_type.value in uploaded_types for doc_type in self._mandatory_documents)
    
    def get_next_expected_document(self, context: WorkflowContext) -> Optional[DocumentType]:
        """Determine which document should be uploaded next"""
        uploaded_types = {doc['document_type'] for doc in context.uploaded_documents.values()}
        
        for doc_type in self._mandatory_documents:
            if doc_type.value not in uploaded_types:
                return doc_type
        
        return None