# app/services/chat/answering/response_validator.py
"""Response validator with CC ≤ 3."""


class ResponseValidator:
    """Validates LLM responses. CC ≤ 3"""
    
    def validate(self, response: dict) -> str:
        """Validate and clean response. CC=3"""
        if "error" in response:
            return f"Error: {response['error']}"
        
        content = response.get("content", "")
        
        if not content or not content.strip():
            return "No content in response"
        
        return content.strip()
