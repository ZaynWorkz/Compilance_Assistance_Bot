class TestConversationRouter:
    
    @pytest.fixture
    def router(self):
        from app.conversation.router import ConversationRouter
        from app.conversation.llm_manager import LLMManager
        llm_manager = LLMManager(api_key="test")
        return ConversationRouter(llm_manager)
    
    def test_off_topic_detection(self, router):
        assert router._is_off_topic("What's the weather today?") == True
        assert router._is_off_topic("I need legal advice") == True
        assert router._is_off_topic("How do I upload a document?") == False
    
    def test_restart_command_detection(self, router):
        assert router._is_restart_command("I want to restart") == True
        assert router._is_restart_command("start over please") == True
        assert router._is_restart_command("upload document") == False
    
    def test_declaration_number_extraction(self, router):
        from app.workflow.state_machine import WorkflowState
        
        result = router._handle_declaration_input(
            "My declaration number is DEC-2024-123456",
            {}
        )
        
        assert result['type'] == 'declaration_number'
        assert result['value'] == 'DEC-2024-123456'
        
        result = router._handle_declaration_input(
            "Invalid number",
            {}
        )
        
        assert result['type'] == 'clarification'