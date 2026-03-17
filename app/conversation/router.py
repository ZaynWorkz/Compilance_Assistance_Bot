# app/conversation/router.py (FIXED)

from typing import Dict, Any, Optional, List
import re
from ..workflow.state_machine import WorkflowState, DocumentType

class ConversationRouter:
    """Routes user messages to appropriate handlers"""
    
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
        self.workflow_keywords = {
            'upload': ['upload', 'attach', 'submit', 'send file'],
            'status': ['status', 'progress', 'where', 'pending'],
            'help': ['help', 'assist', 'guide', 'instruction'],
            'restart': ['restart', 'reset', 'start over', 'begin again'],
            'document': ['document', 'file', 'paper', 'form']
        }
        
        self.off_topic_patterns = [
            r'\b(weather|news|sports|politics|movie|music)\b',
            r'\b(legal advice|lawyer|court|sue)\b',
            r'\b(price|cost|fee|payment)\b',
            r'\b(general (question|query)|unrelated)\b'
        ]
    
    def route_message(self, 
                      message: str, 
                      current_state: WorkflowState, 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route message to appropriate handler based on content and state
        """
        # Check for off-topic queries first
        if self._is_off_topic(message):
            return {
                'type': 'off_topic',
                'response': "I am currently assisting with document upload and compliance verification. Please complete this process or restart the session.",
                'should_respond': True
            }
        
        # Check for workflow commands
        if self._is_restart_command(message):
            return {
                'type': 'restart',
                'response': "Restarting the document upload process.",
                'should_respond': True
            }
        
        # Route based on current state
        if current_state == WorkflowState.AWAITING_DECLARATION_NUMBER:
            return self._handle_declaration_input(message, context)
        elif current_state == WorkflowState.AWAITING_DOCUMENT:
            return self._handle_document_request(message, context)
        elif current_state == WorkflowState.VALIDATION_FAILED:
            return self._handle_validation_failure(message, context)
        elif current_state in [WorkflowState.VALIDATION_SUCCESS, WorkflowState.COMPLETED]:
            return self._handle_completed_workflow(message, context)
        
        # Default to LLM response for workflow-related queries
        return self._get_llm_response(message, current_state, context)
    
    def _is_off_topic(self, message: str) -> bool:
        """Check if message is off-topic"""
        message_lower = message.lower()
        
        # Check against off-topic patterns
        for pattern in self.off_topic_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def _is_restart_command(self, message: str) -> bool:
        """Check if user wants to restart"""
        restart_phrases = ['restart', 'start over', 'reset', 'begin again', 'new session']
        return any(phrase in message.lower() for phrase in restart_phrases)
    
    def _handle_declaration_input(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle declaration number input"""
        # Extract declaration number using regex
        decl_pattern = r'(DEC-\d{4}-\d{6})'
        match = re.search(decl_pattern, message)
        
        if match:
            return {
                'type': 'declaration_number',
                'value': match.group(1),
                'response': f"Declaration number {match.group(1)} received. Please upload the Invoice document.",
                'should_respond': True
            }
        else:
            return {
                'type': 'clarification',
                'response': "Please provide a valid declaration number in format DEC-YYYY-###### (e.g., DEC-2024-123456)",
                'should_respond': True
            }
    
    def _handle_document_request(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document upload requests"""
        # Check if message indicates document upload intent
        upload_intent = any(word in message.lower() for word in ['upload', 'attach', 'file', 'document'])
        
        if upload_intent:
            # Determine which document is expected
            next_doc = context.get('next_expected_document')
            if next_doc:
                if hasattr(next_doc, 'value'):
                    doc_name = next_doc.value.replace('_', ' ').title()
                else:
                    doc_name = str(next_doc).replace('_', ' ').title()
                    
                return {
                    'type': 'document_upload',
                    'expected_document': next_doc,
                    'response': f"Please upload the {doc_name} document.",
                    'should_respond': True
                }
        
        return self._get_llm_response(message, context)
    
    def _handle_validation_failure(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle messages during validation failure state"""
        mismatches = context.get('validation_results', {}).get('mismatches', [])
        
        if mismatches:
            mismatch_docs = list(set([m.get('document_type', 'unknown') for m in mismatches]))
            return {
                'type': 'reupload_request',
                'documents': mismatch_docs,
                'response': f"Validation failed for {', '.join(mismatch_docs)}. Please re-upload these documents.",
                'should_respond': True
            }
        
        return self._get_llm_response(message, context)
    
    def _handle_completed_workflow(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle messages after workflow completion"""
        return {
            'type': 'completed',
            'response': "Document verification is complete. The package has been sent for approval. You can restart the session for a new audit.",
            'should_respond': True
        }
    
    def _get_llm_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get LLM response for workflow-related queries"""
        # For now, return a simple response since we don't have full LLM integration
        return {
            'type': 'llm_response',
            'response': "I'm here to help with document upload. Please follow the instructions to complete the process.",
            'should_Respond': True
        }