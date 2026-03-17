
import pytest
from datetime import datetime
from app.workflow.state_machine import StateMachine, WorkflowState, WorkflowContext, DocumentType

class TestStateMachine:
    
    @pytest.fixture
    def state_machine(self):
        return StateMachine()
    
    @pytest.fixture
    def valid_context(self):
        return WorkflowContext(
            session_id="test-session",
            current_state=WorkflowState.INITIAL,
            declaration_number="DEC-2024-123456",
            uploaded_documents={
                "doc1": {"document_type": "declaration", "extracted_data": {}},
                "doc2": {"document_type": "invoice", "extracted_data": {}},
                "doc3": {"document_type": "packing_list", "extracted_data": {}},
                "doc4": {"document_type": "bol_aws", "extracted_data": {}},
                "doc5": {"document_type": "country_of_origin", "extracted_data": {}},
                "doc6": {"document_type": "delivery_order", "extracted_data": {}}
            }
        )
    
    def test_initial_state_transition(self, state_machine):
        context = WorkflowContext(session_id="test", current_state=WorkflowState.INITIAL)
        assert state_machine.can_transition(
            WorkflowState.INITIAL, 
            WorkflowState.AWAITING_DECLARATION_NUMBER, 
            context
        ) == True
    
    def test_cannot_skip_declaration(self, state_machine):
        context = WorkflowContext(session_id="test", current_state=WorkflowState.INITIAL)
        assert state_machine.can_transition(
            WorkflowState.INITIAL, 
            WorkflowState.AWAITING_DOCUMENT, 
            context
        ) == False
    
    def test_all_mandatory_documents_check(self, state_machine, valid_context):
        assert state_machine._all_mandatory_documents_uploaded(valid_context) == True
        
        # Remove one document
        del valid_context.uploaded_documents["doc6"]
        assert state_machine._all_mandatory_documents_uploaded(valid_context) == False
    
    def test_next_expected_document(self, state_machine):
        context = WorkflowContext(
            session_id="test",
            current_state=WorkflowState.AWAITING_DOCUMENT,
            uploaded_documents={
                "doc1": {"document_type": "declaration"}
            }
        )
        
        next_doc = state_machine.get_next_expected_document(context)
        assert next_doc == DocumentType.INVOICE
        
        # Add all documents
        for doc_type in ['invoice', 'packing_list', 'bol_aws', 'country_of_origin', 'delivery_order']:
            context.uploaded_documents[f"doc_{doc_type}"] = {"document_type": doc_type}
        
        next_doc = state_machine.get_next_expected_document(context)
        assert next_doc is None