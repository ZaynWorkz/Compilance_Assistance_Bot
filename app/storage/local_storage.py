# app/main.py (UPDATE THIS)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import datetime


import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Import from utils first
from app.utils.context import WorkflowContext
from app.utils.logger import setup_logging

# Then import from other modules
from app.components.otp_input import render_declaration_input
from app.components.summary_grid import render_summary_grid
from app.session.state_manager import SessionStateManager
from app.session.attempt_tracker import AttemptTracker
from app.database.postgres_client import PostgresClient
from app.workflow.state_machine import WorkflowState, StateMachine
from app.validation.engine import ValidationEngine
from app.document.processor import DocumentProcessor

# Setup logging
logger = setup_logging()

# app/storage/local_storage.py (FIXED VERSION)

"""
Local file storage manager for uploaded documents
"""

class LocalStorageManager:
    """Manage local file storage for uploaded documents"""
    
    def __init__(self, base_path: str = "uploads"):
        """
        Initialize storage manager
        
        Args:
            base_path: Root directory for all uploads
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        print(f"✅ Storage initialized at: {self.base_path.absolute()}")
    
    def save_file(self, file, declaration_number: str, document_type: str) -> str:
        """
        Save uploaded file to organized folder structure
        
        Args:
            file: Uploaded file object (from Streamlit)
            declaration_number: Declaration number for folder naming
            document_type: Type of document (declaration, invoice, etc.)
            
        Returns:
            str: Path to saved file
        """
        # Sanitize declaration number for folder name
        safe_decl = self._sanitize_filename(declaration_number)
        
        # Create declaration folder
        decl_folder = self.base_path / safe_decl
        decl_folder.mkdir(exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = Path(file.name).stem
        extension = Path(file.name).suffix
        
        filename = f"{document_type}_{timestamp}_{original_name}{extension}"
        file_path = decl_folder / filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file.getbuffer())
        
        print(f"✅ File saved: {file_path}")
        return str(file_path)
    
    def get_file(self, declaration_number: str, document_type: str) -> Optional[str]:
        """
        Get the most recent file of a specific type for a declaration
        
        Args:
            declaration_number: Declaration number
            document_type: Type of document
            
        Returns:
            Optional[str]: Path to file if found, None otherwise
        """
        decl_folder = self.base_path / self._sanitize_filename(declaration_number)
        
        if not decl_folder.exists():
            return None
        
        # Find all files of this document type
        files = list(decl_folder.glob(f"{document_type}_*"))
        if not files:
            return None
        
        # Return the most recent
        return str(max(files, key=os.path.getctime))
    
    def list_files(self, declaration_number: str) -> List[str]:
        """
        List all files for a declaration
        
        Args:
            declaration_number: Declaration number
            
        Returns:
            List[str]: List of file paths
        """
        decl_folder = self.base_path / self._sanitize_filename(declaration_number)
        
        if not decl_folder.exists():
            return []
        
        return [str(f) for f in decl_folder.glob("*") if f.is_file()]
    
    def get_declaration_folder(self, declaration_number: str) -> Optional[str]:
        """
        Get folder path for a declaration
        
        Args:
            declaration_number: Declaration number
            
        Returns:
            Optional[str]: Folder path if exists, None otherwise
        """
        folder = self.base_path / self._sanitize_filename(declaration_number)
        return str(folder) if folder.exists() else None
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a specific file
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
        except Exception as e:
            print(f"Error deleting file: {e}")
        return False
    
    def delete_declaration_folder(self, declaration_number: str) -> bool:
        """
        Delete entire declaration folder and all files
        
        Args:
            declaration_number: Declaration number
            
        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            folder = self.base_path / self._sanitize_filename(declaration_number)
            if folder.exists():
                shutil.rmtree(folder)
                return True
        except Exception as e:
            print(f"Error deleting folder: {e}")
        return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for filesystem
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()


# Optional: Quick test function
def test_storage():
    """Test the storage manager"""
    storage = LocalStorageManager()
    print(f"Storage path: {storage.base_path}")
    
    # Test file listing (without actual file)
    files = storage.list_files("TEST-123")
    print(f"Files for TEST-123: {files}")


if __name__ == "__main__":
    test_storage()