# app/app.py (UPDATED VERSION)

import time

import streamlit as st
from pathlib import Path
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import all modules
from app.validation.smart_validator import SmartValidator
from app.components.otp_input import render_declaration_input
from app.components.summary_grid import render_summary_grid
from app.session.state_manager import SessionStateManager
from app.session.attempt_tracker import AttemptTracker
from app.storage.local_storage import LocalStorageManager
from app.database.postgres_client import PostgresClient
from app.workflow.state_machine import WorkflowState
from app.validation.engine import ValidationEngine
from app.document.processor import DocumentProcessor
from app.utils.logger import setup_logging

# Setup logging
logger = setup_logging()

# Page config
st.set_page_config(
    page_title="Compliance Assistant",
    page_icon="📋",
    layout="wide"
)

class ComplianceApp:
    def __init__(self):
        """Initialize the application"""
        self.session_manager = SessionStateManager()
        self.attempt_tracker = AttemptTracker(max_attempts=3)
        self.storage_manager = LocalStorageManager(base_path="uploads")
        self.db_client = PostgresClient()  # Will connect to PostgreSQL
        self.doc_processor = DocumentProcessor()
        self.validation_engine = ValidationEngine() 
        self.smart_validator = SmartValidator()
        
        # Document order with optional flags
        self.document_order = [
            {'type': 'declaration', 'label': '📄 Declaration', 'mandatory': True},
            {'type': 'invoice', 'label': '💰 Invoice', 'mandatory': True},
            {'type': 'coo', 'label': '🌍 Certificate of Origin', 'mandatory': True},
            {'type': 'mawb', 'label': '✈️ MAWB', 'mandatory': True},
            {'type': 'packing_list', 'label': '📦 Packing List', 'mandatory': False},
            {'type': 'delivery_order', 'label': '📋 Delivery Order', 'mandatory': False}
        ] 
        print("🔍 Document Order Type Check:")
        for i, item in enumerate(self.document_order):
            print(f"  Item {i}: type={type(item)}, value={item}")
        print("✅ AFTER FIX - document_order[0]:", self.document_order[0])
        print("✅ Type:", type(self.document_order[0]))
        
        # Initialize session state
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state variables"""
        if 'current_step' not in st.session_state:
            st.session_state.current_step = 'declaration_number'
        if 'declaration_number' not in st.session_state:
            st.session_state.declaration_number = None
        if 'declaration_date' not in st.session_state:
            st.session_state.declaration_date = None
        if 'uploaded_docs' not in st.session_state:
            st.session_state.uploaded_docs = {}
        if 'current_doc_index' not in st.session_state:
            st.session_state.current_doc_index = 0
        if 'session_aborted' not in st.session_state:
            st.session_state.session_aborted = False
        if 'show_summary' not in st.session_state:
            st.session_state.show_summary = False
    
    def run(self):
        """Main application flow"""
        
        # Sidebar
        with st.sidebar:
            self._render_sidebar()
        
        # Main content
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Check if session aborted
            if st.session_state.session_aborted:
                self._render_aborted_session()
                return
            
            # Render appropriate step
            if st.session_state.current_step == 'declaration_number':
                self._render_declaration_step()
            elif st.session_state.current_step == 'declaration_date':
                self._render_date_step()
            elif st.session_state.current_step == 'document_upload':
                self._render_upload_step()
            elif st.session_state.show_summary:
                self._render_summary_step()
        
        with col2:
            self._render_status_panel()
    
    def _process_upload(self, file, doc_info):
        if isinstance(doc_info, tuple):
            doc_type = doc_info[0]
            doc_label = doc_info[1]
            is_mandatory = True  # Assume mandatory for old format
        else:
            doc_type = doc_info.get('type')
            doc_label = doc_info.get('label')
            is_mandatory = doc_info.get('mandatory', True)
        
        print(f"\n🔍 PROCESSING UPLOAD:")
        print(f"  Expected: {doc_type}")
        
        # Process document
        result = self.doc_processor.process_document(file)
        
        print(f"  Classified as: {result['document_type']}")
        
        # Check if document type matches expected
        if result['document_type'] != doc_type:
            # Failed attempt
            can_proceed, message = self.attempt_tracker.register_attempt(
                doc_type, success=False
            )
            
            if not can_proceed:
                st.session_state.session_aborted = True
                st.error("❌ Too many failed attempts. Session aborted.")
                st.rerun()
                return
            
            attempts_data = self.attempt_tracker.get_attempts(doc_type)
            st.error(f"❌ Wrong document type. Expected {doc_label}. {attempts_data['remaining']} attempts left.")
            return
        
        # Success!
        self.attempt_tracker.register_attempt(doc_type, success=True)
        
        # Save file
        file_path = self.storage_manager.save_file(
            file,
            st.session_state.declaration_number,
            doc_type
        )
        
        # Store in session
        file_data = {
            'filename': file.name,
            'file_path': file_path,
            'document_type': doc_type,
            'extracted_data': result.get('extracted_data', {}),
            'validation': {'status': 'approved'}
        }
        
        if 'uploaded_docs' not in st.session_state:
            st.session_state.uploaded_docs = {}
        
        st.session_state.uploaded_docs[doc_type] = file_data
        
        # Auto-save draft
        self._auto_save_draft()
        
        st.success(f"✅ {doc_label} approved!")
        
        # Move to next document
        st.session_state.current_doc_index = st.session_state.get('current_doc_index', 0) + 1
        st.rerun()

    def _render_sidebar(self):
        """Render sidebar with session info"""
        st.markdown("### 📋 Session Info")
        
        context = self.session_manager.get_context()
        
        # Session status
        st.markdown(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
        if hasattr(context.current_state, 'name'):
            # It's an enum
            state_name = context.current_state.name
        else:
            # It's already a string
            state_name = str(context.current_state)
        st.markdown(f"**Current State:** `{state_name}`")
        st.markdown(f"**Last Activity:** {context.last_activity.strftime('%H:%M:%S')}")
        
        st.divider()
        
        # Progress
        uploaded = len(st.session_state.get('uploaded_docs', {}))
        total = len(self.document_order)
        st.progress(uploaded / total, text=f"Progress: {uploaded}/{total}")
        
        # Show uploaded docs
        if uploaded > 0:
            st.markdown("### ✅ Uploaded")
            for i in range(uploaded):
                doc_info = self.document_order[i]
                if isinstance(doc_info, dict):
                    doc_label = doc_info.get('label', 'Unknown')
                else:
                    doc_label = doc_info[1]  # fallback for tuples
                st.markdown(f"- {doc_label}")
        
        st.divider()
        
        # Restart button
        if st.button("🔄 Restart Session", use_container_width=True):
            st.session_state.restart_requested = True
            st.rerun()
    # app/main.py - Add this method to your ComplianceApp class

    def validate_declaration_format(self, decl_number: str) -> bool:
        """
        Validate declaration number format
        Expected format: 101-25123867-24 (3 digits - 8 digits - 2 digits)
        """
        import re
        
        if not decl_number:
            return False
        
        # Pattern for declaration number
        pattern = r'^\d{3}-\d{8}-\d{2}$'
        
        # Also accept without hyphens? Uncomment if needed
        # pattern = r'^\d{13}$'  # 13 digits without hyphens
        
        is_valid = bool(re.match(pattern, decl_number))
        
        if is_valid:
            print(f"✅ Valid declaration format: {decl_number}")
        else:
            print(f"❌ Invalid declaration format: {decl_number}")
        
        return is_valid
        
    def _render_declaration_step(self):
        """Step 1: Enter declaration number (OTP style)"""
        st.markdown("## 👋 Welcome, Uploader!")
        
        # OTP-style input
        decl_number = render_declaration_input()
        
        if decl_number:
            # Validate format
            if self.validate_declaration_format(decl_number):
                st.session_state.declaration_number = decl_number
                st.session_state.current_step = 'declaration_date'
                
                # Create record in database
                self.db_client.create_declaration(decl_number)
                
                st.rerun()
            else:
                st.error("❌ Invalid format. Use: 101-25123867-24")
    
    def _render_date_step(self):
        """Step 2: Enter declaration date"""
        st.markdown(f"## 📅 Declaration Date for `{st.session_state.declaration_number}`")
        
        # Date input
        date = st.date_input(
            "Enter Declaration Date",
            value=None,
            format="DD/MM/YYYY"
        )
        
        if date:
            st.session_state.declaration_date = date
            st.session_state.current_step = 'document_upload'
            
            # Update database
            self.db_client.update_document(
                st.session_state.declaration_number,
                'metadata',
                {'declaration_date': date.isoformat()}
            )
            
            st.rerun()
    
    # app/main.py - Updated _render_upload_step

    # app/main.py - Updated _render_upload_step

    def _render_upload_step(self):
        """Step 3: Upload documents one by one"""
        
        current_idx = st.session_state.get('current_doc_index', 0)
        
        if current_idx >= len(self.document_order):
            self._validate_and_show_results()
            return
        
        # Get current document info
        doc_info = self.document_order[current_idx]
        
        # 🔥 FIX: Handle both tuple and dictionary formats
        if isinstance(doc_info, tuple):
            # Old format: (type, label)
            doc_type = doc_info[0]
            doc_label = doc_info[1]
            # Assume first 4 are mandatory, rest optional
            is_mandatory = current_idx < 4
        else:
            # New format: dictionary
            doc_type = doc_info.get('type', 'unknown')
            doc_label = doc_info.get('label', 'Unknown')
            is_mandatory = doc_info.get('mandatory', True)
        
        # Create header
        tag = " (Required)" if is_mandatory else " (Optional)"
        st.markdown(f"## 📤 Upload {doc_label}{tag}")
        
        # Progress for mandatory docs only
        uploaded_docs = st.session_state.get('uploaded_docs', {})
        
        # Count mandatory uploaded
        mandatory_uploaded = 0
        for idx, d in enumerate(self.document_order[:current_idx]):
            if isinstance(d, tuple):
                # Old format
                doc_type_check = d[0]
                is_mandatory_check = idx < 4
            else:
                # New format
                doc_type_check = d.get('type')
                is_mandatory_check = d.get('mandatory', False)
            
            if is_mandatory_check and doc_type_check in uploaded_docs:
                mandatory_uploaded += 1
        
        total_mandatory = 4  # We know we have 4 mandatory docs
        
        if total_mandatory > 0:
            st.progress(mandatory_uploaded / total_mandatory, 
                    text=f"Mandatory documents: {mandatory_uploaded}/{total_mandatory}")
        
        # Show optional notice and SKIP button
        if not is_mandatory:
            st.info("⚠️ This document is optional. You can upload now or skip and continue.")
            
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("⏭️ Skip for now", key=f"skip_{doc_type}"):
                    # Mark as skipped in session
                    if 'skipped_docs' not in st.session_state:
                        st.session_state.skipped_docs = []
                    st.session_state.skipped_docs.append(doc_type)
                    
                    # Move to next document
                    st.session_state.current_doc_index = current_idx + 1
                    st.rerun()
        # Add temporarily in _render_upload_step
        st.write("Debug - document_order type:", type(self.document_order[0]))
        st.write("Debug - first item:", self.document_order[0])

        # File uploader
        uploaded_file = st.file_uploader(
            f"Choose {doc_label} file",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            key=f"uploader_{doc_type}_{current_idx}"
        )
        
        if uploaded_file:
            # Pass the whole doc_info to _process_upload
            self._process_upload(uploaded_file, doc_info)

    def _render_summary_step(self):
        """Step 4: Show summary grid"""
        st.markdown("## 📋 Document Summary")
    
    # Show validation status
        if 'validation_result' in st.session_state:
            result = st.session_state.validation_result
            status = result['status']
            
            if status == 'success':
                st.success("✅ All validations passed!")
            elif status == 'warning':
                st.warning("⚠️ Some warnings exist - review below")
            
            # Show summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Documents Uploaded", len(st.session_state.uploaded_docs))
            with col2:
                st.metric("Mandatory Docs", len([d for d in self.document_order if d['mandatory']]))
            with col3:
                st.metric("Warnings", len(result['mismatches']))
        
        # Render the grid (from your components)
        from app.components.summary_grid import render_summary_grid
        
        submitted = render_summary_grid(
            st.session_state.declaration_number,
            st.session_state.uploaded_docs
        )
        
        if submitted:
            # Complete the process
            self.db_client.complete_declaration(
                st.session_state.declaration_number
            )
            
            # Save final state
            self.history_manager.save_declaration_state(
                st.session_state.declaration_number,
                {
                    'declaration_date': st.session_state.declaration_date,
                    'uploaded_docs': st.session_state.uploaded_docs,
                    'validation_result': st.session_state.validation_result,
                    'current_step': 'completed'
                }
            )
            
            st.balloons()
            st.success("✅ Documents submitted for approval!")
            
            # Show success message
            st.markdown("""
            ### 🎉 Submission Complete!
            
            Your documents have been successfully submitted to the auditor.
            You will receive notification once reviewed.
            
            Thank you for using Compliance Assistant!
            """)
            
            if st.button("📤 Start New Session"):
                self._restart_session()
        
    def _render_aborted_session(self):
        """Render aborted session message"""
        st.error("## ❌ Session Aborted")
        st.markdown("""
        Too many failed upload attempts. 
        
        **Please restart the session with valid documents.**
        
        Common issues:
        - Wrong document type uploaded
        - Missing required fields
        - Poor quality scans
        """)
        
        if st.button("🔄 Restart Session"):
            self._restart_session()
    
    def _render_status_panel(self):
   
        st.markdown("### 📊 Status")
        
        # Declaration info
        if hasattr(st.session_state, 'declaration_number') and st.session_state.declaration_number:
            st.info(f"**DEC:** {st.session_state.declaration_number}")
        
        if hasattr(st.session_state, 'declaration_date') and st.session_state.declaration_date:
            st.info(f"**Date:** {st.session_state.declaration_date}")
        
        st.divider()
        
        # Validation status
        if hasattr(st.session_state, 'validation_result') and st.session_state.validation_result:
            result = st.session_state.validation_result
            status_colors = {
                'success': '🟢',
                'warning': '🟡',
                'failed': '🔴',
                'incomplete': '⚪'
            }
            status_icon = status_colors.get(result.get('status', ''), '⚪')
            st.markdown(f"{status_icon} **Status:** {result.get('status', 'Unknown').title()}")
            
            mismatches = result.get('mismatches', [])
            if mismatches:
                st.markdown(f"⚠️ **Issues:** {len(mismatches)}")
        
        st.divider()
        
        # Document queue
        st.markdown("#### 📋 Document Queue")
        
        # Get current index safely
        current_idx = st.session_state.get('current_doc_index', 0)
        
        for idx, doc_info in enumerate(self.document_order):
            # Handle both tuple and dictionary formats
            if isinstance(doc_info, tuple):
                # Old format
                doc_type = doc_info[0]
                doc_label = doc_info[1]
                is_mandatory = True
            else:
                # New format (dictionary)
                doc_type = doc_info.get('type', 'unknown')
                doc_label = doc_info.get('label', 'Unknown')
                is_mandatory = doc_info.get('mandatory', True)
            
            # Get uploaded docs safely
            uploaded_docs = st.session_state.get('uploaded_docs', {})
            
            # Determine status
            if doc_type in uploaded_docs:
                st.markdown(f"✅ **{doc_label}**")
            elif idx == current_idx:
                st.markdown(f"⏳ **{doc_label}**")
            else:
                if is_mandatory:
                    st.markdown(f"⏱️ **{doc_label}**")
                else:
                    st.markdown(f"📎 **{doc_label}**")

    def _auto_save_draft(self):
        """Save current progress to database"""
        
        if not st.session_state.get('declaration_number'):
            return
        
        draft_data = {
            'declaration_number': st.session_state.declaration_number,
            'declaration_date': st.session_state.get('declaration_date'),
            'uploaded_docs': st.session_state.get('uploaded_docs', {}),
            'skipped_docs': st.session_state.get('skipped_docs', []),
            'current_step': st.session_state.get('current_step'),
            'current_doc_index': st.session_state.get('current_doc_index', 0),
            'last_updated': str(datetime.now()),
            'status': 'draft'
        }
        
        # Save to database
        self.db_client.save_draft(draft_data)
        print(f"💾 Auto-saved draft for {st.session_state.declaration_number}")


    def _check_for_existing_draft(self, declaration_number):
        """Check if there's a draft for this declaration"""
        
        draft = self.db_client.get_draft(declaration_number)
        
        if draft:
            st.info(f"📂 Found existing draft for {declaration_number}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Resume Draft"):
                    self._restore_draft(draft)
            with col2:
                if st.button("🆕 Start Fresh"):
                    self._clear_draft(declaration_number)
            return True
        return False

    def _restore_draft(self, draft):
        """Restore a saved draft"""
        
        st.session_state.declaration_number = draft['declaration_number']
        st.session_state.declaration_date = draft.get('declaration_date')
        st.session_state.uploaded_docs = draft.get('uploaded_docs', {})
        st.session_state.skipped_docs = draft.get('skipped_docs', [])
        st.session_state.current_step = draft.get('current_step', 'document_upload')
        st.session_state.current_doc_index = draft.get('current_doc_index', 0)
        
        # Show welcome back message
        pending = self._get_pending_documents()
        if pending:
            st.info(f"📋 You have {len(pending)} documents pending: {', '.join(pending)}")
        
        st.rerun()

    # app/main.py - Add pending docs display


    def _get_pending_documents(self):
        """Get list of still-needed documents"""
        
        uploaded = set(st.session_state.get('uploaded_docs', {}).keys())
        skipped = set(st.session_state.get('skipped_docs', []))
        
        pending = []
        for doc in self.document_order:
            # 🔥 FIX: Handle both tuple and dictionary formats
            if isinstance(doc, tuple):
                # Old format: (type, label)
                doc_type = doc[0]
                doc_label = doc[1]
                # Assume first 4 are mandatory
                is_mandatory = self.document_order.index(doc) < 4
            else:
                # New format: dictionary
                doc_type = doc.get('type', 'unknown')
                doc_label = doc.get('label', 'Unknown')
                is_mandatory = doc.get('mandatory', True)
            
            if is_mandatory and doc_type not in uploaded:
                pending.append(doc_label)
            elif not is_mandatory and doc_type not in uploaded and doc_type not in skipped:
                pending.append(f"{doc_label} (optional)")
        
        return pending


    def _render_status_panel(self):
        """Render right panel with status"""
        st.markdown("### 📊 Status")
        
        # Declaration info
        if st.session_state.get('declaration_number'):
            st.info(f"**DEC:** {st.session_state.declaration_number}")
        
        if st.session_state.get('declaration_date'):
            st.info(f"**Date:** {st.session_state.declaration_date}")
        
        st.divider()
        
        # Show pending documents
        pending = self._get_pending_documents()
        if pending:
            st.warning(f"⏳ **Pending:** {len(pending)} documents")
            with st.expander("📋 Pending Documents"):
                for doc in pending:
                    st.markdown(f"• {doc}")
        else:
            st.success("✅ All documents uploaded!")
        
        st.divider()
        
        # Document queue
        st.markdown("#### 📋 Document Queue")
        
        current_idx = st.session_state.get('current_doc_index', 0)
        uploaded_docs = st.session_state.get('uploaded_docs', {})
        
        for idx, doc_info in enumerate(self.document_order):
            # 🔥 FIX: Handle both tuple and dictionary formats
            if isinstance(doc_info, tuple):
                doc_type = doc_info[0]
                doc_label = doc_info[1]
            else:
                doc_type = doc_info.get('type', 'unknown')
                doc_label = doc_info.get('label', 'Unknown')
            
            if doc_type in uploaded_docs:
                st.markdown(f"✅ **{doc_label}**")
            elif idx == current_idx:
                st.markdown(f"⏳ **{doc_label}**")
            else:
                st.markdown(f"⏱️ **{doc_label}**")

    def _validate_and_show_results(self):
        """Run smart validation and show results"""
        
        st.markdown("## 🔍 Validating Documents...")
        
        with st.spinner("Running smart validation..."):
            # Run smart validator
            validation_result = self.smart_validator.validate(st.session_state.uploaded_docs)
            
            # Store in session
            st.session_state.validation_result = validation_result
            
            # Show results based on status
            if validation_result['status'] == 'success':
                st.balloons()
                st.success("✅ All documents validated successfully!")
                st.session_state.show_summary = True
                
            elif validation_result['status'] == 'warning':
                st.warning("⚠️ Documents validated with warnings")
                self._show_validation_warnings(validation_result)
                st.session_state.show_summary = True
                
            elif validation_result['status'] == 'failed':
                st.error("❌ Validation failed!")
                self._show_validation_errors(validation_result)
                
                # Allow re-upload of problematic docs
                if st.button("📤 Re-upload Problematic Documents"):
                    # Reset index to first problematic doc
                    st.session_state.current_doc_index = 0
                    st.rerun()
                    
            else:  # incomplete
                st.warning("⏳ Missing required documents")
                self._show_missing_documents(validation_result)
                
                # Continue with missing mandatory docs
                if st.button("Continue Upload"):
                    st.session_state.current_doc_index = 0
                    st.rerun()
        
    def _validate_declaration_format(self, decl_number):
        """Validate declaration number format"""
        import re
        pattern = r'^\d{3}-\d{8}-\d{2}$'
        return bool(re.match(pattern, decl_number))
    
    def _validate_document_data(self, data, doc_type):
        """Validate document-specific data"""
        required_fields = {
            'declaration': ['declaration_number'],
            'invoice': ['invoice_number', 'total_value'],
            'packing_list': ['total_packages'],
            'bol_aws': ['bol_number'],
            'country_of_origin': ['origin_country'],
            'delivery_order': ['delivery_order_number']
        }
        
        if doc_type in required_fields:
            missing = [f for f in required_fields[doc_type] if f not in data]
            if missing:
                return False, f"Missing fields: {', '.join(missing)}"
        
        return True, "Valid"
    
    def validate_coo_with_invoice(coo_data, invoice_data):
        """Validate that COO references the correct invoice"""
        
        if not coo_data or not invoice_data:
            return False, "Missing COO or Invoice data"
        
        coo_invoice = coo_data.get('referenced_invoice')
        invoice_number = invoice_data.get('invoice_number')
        
        if coo_invoice and invoice_number:
            if str(coo_invoice) == str(invoice_number):
                print(f"✅ CHAIN VALID: COO references Invoice #{invoice_number}")
                return True, "Chain validation passed"
            else:
                print(f"❌ CHAIN INVALID: COO references #{coo_invoice} but Invoice is #{invoice_number}")
                return False, f"Invoice mismatch: COO says {coo_invoice}, Invoice says {invoice_number}"
        
        return False, "Missing invoice reference in COO"
        
    def _restart_session(self):
        """Restart the session"""
        for key in ['current_step', 'declaration_number', 'declaration_date',
                    'uploaded_docs', 'current_doc_index', 'session_aborted',
                    'show_summary']:
            if key in st.session_state:
                del st.session_state[key]
        
        self.attempt_tracker.reset()
        st.rerun()

    def _show_validation_warnings(self, result):
        """Show validation warnings"""
        with st.expander("⚠️ Validation Warnings", expanded=True):
            for mismatch in result['mismatches']:
                if mismatch['severity'] in ['medium', 'low']:
                    st.warning(f"• {mismatch['message']}")
            
            # Show optional missing docs
            if result['missing_optional']:
                st.info(f"Optional documents not uploaded: {', '.join(result['missing_optional'])}")

    def _show_validation_errors(self, result):
        """Show validation errors"""
        with st.expander("❌ Validation Errors", expanded=True):
            for mismatch in result['mismatches']:
                if mismatch['severity'] in ['high', 'critical']:
                    st.error(f"• {mismatch['message']}")
            
            if not result['chain_valid']:
                st.error("• Critical chain validation failed")

    def _show_missing_documents(self, result):
        """Show missing documents"""
        with st.expander("📋 Missing Documents", expanded=True):
            if result['missing_mandatory']:
                st.error(f"Missing mandatory: {', '.join(result['missing_mandatory'])}")
            if result['missing_optional']:
                st.info(f"Missing optional: {', '.join(result['missing_optional'])}")


def main():

    app = ComplianceApp()
    app.run()

if __name__ == "__main__":
    main()