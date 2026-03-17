# app/session/state_manager.py

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
from ..workflow.state_machine import WorkflowContext, WorkflowState, StateMachine

class SessionStateManager:
    """Manages Streamlit session state"""
    
    def __init__(self):
        self.state_machine = StateMachine()
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize or restore session state"""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.workflow_context = WorkflowContext(
                session_id=st.session_state.session_id,
                current_state=WorkflowState.INITIAL.name  # Use .name, not the enum
            )
            st.session_state.messages = []
            st.session_state.uploaded_files = {}
            st.session_state.error_count = 0
    
    def get_context(self) -> WorkflowContext:
        """Get current workflow context"""
        return st.session_state.workflow_context
        
    def update_context(self, **kwargs):
        """Update workflow context with validation"""
        context = self.get_context()
        
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)
        
        context.last_activity = datetime.now()
        st.session_state.workflow_context = context
    
    def transition_to(self, new_state: WorkflowState, **context_updates):
        """Attempt state transition with validation"""
        context = self.get_context()
        
        # Update context with any provided values
        if context_updates:
            self.update_context(**context_updates)
            context = self.get_context()
        
        # Validate transition
        if self.state_machine.can_transition(context.current_state, new_state, context):
            old_state = context.current_state
            self.update_context(current_state=new_state)
            
            # Log transition
            self._log_transition(old_state, new_state)
            return True
        else:
            self._handle_invalid_transition(new_state)
            return False
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to conversation history"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        st.session_state.messages.append(message)
        
        # Keep only last 50 messages for performance
        if len(st.session_state.messages) > 50:
            st.session_state.messages = st.session_state.messages[-50:]
    
    def store_document(self, document_type: str, file_data: Dict[str, Any]):
        """Store uploaded document with metadata"""
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = {}
        
        document_id = f"{document_type}_{datetime.now().timestamp()}"
        
        st.session_state.uploaded_files[document_id] = {
            'document_type': document_type,
            'filename': file_data.get('name'),
            'upload_time': datetime.now().isoformat(),
            'size': file_data.get('size'),
            'validation_status': 'pending',
            'extracted_data': file_data.get('extracted_data', {})
        }
        
        # Update workflow context
        context = self.get_context()
        context.uploaded_documents[document_id] = st.session_state.uploaded_files[document_id]
        self.update_context(uploaded_documents=context.uploaded_documents)
        
        return document_id
    
    def is_session_valid(self) -> bool:
        """Check if session is still valid (not timed out)"""
        context = self.get_context()
        time_diff = datetime.now() - context.last_activity
        
        if time_diff > timedelta(minutes=self.SESSION_TIMEOUT_MINUTES):
            self.add_message('system', 'Session timed out due to inactivity. Please restart.')
            return False
        
        return True
    
    def can_retry(self) -> bool:
        """Check if user can retry after failure"""
        context = self.get_context()
        return context.retry_count < self.MAX_RETRY_ATTEMPTS
    
    def increment_retry(self):
        """Increment retry count"""
        context = self.get_context()
        context.retry_count += 1
        self.update_context(retry_count=context.retry_count)
    
    def reset_session(self):
        """Reset session to initial state"""
        for key in ['session_id', 'workflow_context', 'messages', 'uploaded_files', 'validation_history']:
            if key in st.session_state:
                del st.session_state[key]
        
        self._initialize_session()
        self.add_message('assistant', 'Session restarted. Ready to begin document upload process.')
    
    def _log_transition(self, old_state: WorkflowState, new_state: WorkflowState):
        """Log state transition for audit"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.session_id,
            'from_state': old_state.name,
            'to_state': new_state.name
        }
        
        if 'validation_history' not in st.session_state:
            st.session_state.validation_history = []
        
        st.session_state.validation_history.append(log_entry)
    
    def _handle_invalid_transition(self, attempted_state: WorkflowState):
        """Handle invalid state transition attempts"""
        context = self.get_context()
        st.session_state.error_count += 1
        
        error_msg = f"Invalid state transition from {context.current_state.name} to {attempted_state.name}"
        context.errors.append({
            'timestamp': datetime.now().isoformat(),
            'error': error_msg
        })
        
        self.add_message('system', f"Error: {error_msg}. Please follow the workflow correctly.")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session for debugging/audit"""
        return {
            'session_id': st.session_state.session_id,
            'current_state': st.session_state.workflow_context.current_state.name,
            'messages_count': len(st.session_state.messages),
            'documents_uploaded': len(st.session_state.uploaded_files),
            'error_count': st.session_state.error_count,
            'validation_history': st.session_state.validation_history[-5:],  # Last 5 transitions
            'last_activity': st.session_state.workflow_context.last_activity.isoformat()
        }