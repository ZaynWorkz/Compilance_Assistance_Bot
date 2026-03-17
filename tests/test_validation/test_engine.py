class TestValidationEngine:
    
    @pytest.fixture
    def validation_engine(self):
        from app.validation.engine import ValidationEngine
        return ValidationEngine()
    
    def test_declaration_format_validation(self, validation_engine):
        assert validation_engine._validate_declaration_format("DEC-2024-123456") == True
        assert validation_engine._validate_declaration_format("INVALID-123") == False
        assert validation_engine._validate_declaration_format("") == False
    
    def test_missing_documents_detection(self, validation_engine):
        uploaded_docs = {
            "doc1": {"document_type": "declaration"},
            "doc2": {"document_type": "invoice"}
        }
        
        missing = validation_engine._check_missing_documents(uploaded_docs)
        assert "packing_list" in missing
        assert "bol_aws" in missing
        assert len(missing) == 4  # 4 missing out of 6 mandatory
    
    def test_primary_key_consistency(self, validation_engine):
        declaration_number = "DEC-2024-123456"
        uploaded_docs = {
            "doc1": {
                "document_type": "declaration",
                "extracted_data": {"declaration_number": "DEC-2024-123456"}
            },
            "doc2": {
                "document_type": "invoice",
                "extracted_data": {"declaration_number": "DEC-2024-123456"}
            },
            "doc3": {
                "document_type": "packing_list",
                "extracted_data": {"declaration_number": "DEC-2024-123456"}
            }
        }
        
        mismatches = validation_engine._check_primary_key_consistency(declaration_number, uploaded_docs)
        assert len(mismatches) == 0
        
        # Add mismatched document
        uploaded_docs["doc4"] = {
            "document_type": "bol_aws",
            "extracted_data": {"declaration_number": "DEC-2024-999999"}
        }
        
        mismatches = validation_engine._check_primary_key_consistency(declaration_number, uploaded_docs)
        assert len(mismatches) == 1
        assert mismatches[0]['document_type'] == "bol_aws"