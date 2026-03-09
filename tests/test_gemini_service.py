import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.gemini_service import GeminiTranslationService
import json

@pytest.fixture
def api_key():
    return "dummy_api_key"

@pytest.fixture
def service(api_key):
    # Mock genai to avoid actual API calls during tests
    import google.generativeai as genai
    genai.configure = MagicMock()
    genai.GenerativeModel = MagicMock()
    return GeminiTranslationService(api_key=api_key)

@pytest.mark.asyncio
async def test_extract_data_from_image_with_schema(service):
    # Setup mock response
    mock_model = AsyncMock()
    service.model = mock_model
    
    expected_response = {
        "metadata": {"doc_type": "diploma", "language": "ru"},
        "fields": {"fullname": "Ivanov Ivan"},
        "tables": {"grades": [{"subject": "Math", "score": "5"}]}
    }
    
    mock_response = MagicMock()
    mock_response.text = json.dumps(expected_response)
    mock_model.generate_content_async.return_value = mock_response
    
    schema = {
        "type": "object",
        "properties": {
            "metadata": {"type": "object"},
            "fields": {"type": "object"},
            "tables": {"type": "object"}
        }
    }
    
    # Needs a dummy image path
    import tempfile
    from PIL import Image
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        img = Image.new('RGB', (10, 10))
        img.save(tmp, format="JPEG")
        tmp_path = tmp.name
        tmp.close()
    
    try:
        # Call the method
        result = await service.extract_data_from_image(
            image_path=tmp_path,
            json_schema=schema
        )
        
        # Verify result
        assert result == expected_response
        
        # Verify prompt construction
        call_args = mock_model.generate_content_async.call_args
        assert call_args is not None
        
        contents = call_args[0][0] # First argument is contents
        prompt_used = contents[0]
        
        # Ensure schema is appended to prompt
        assert "Return strictly valid JSON according to the provided schema" in prompt_used
        assert "metadata" in prompt_used
    finally:
        import os
        try:
            os.remove(tmp_path)
        except OSError:
            pass

@pytest.mark.asyncio
async def test_extract_data_from_image_test_response(service):
    test_resp = {"status": "ok"}
    result = await service.extract_data_from_image(test_json_response=test_resp)
    assert result == test_resp
