
import os
import sys
# Add src to python path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from service.ai_service import AIService
from unittest.mock import MagicMock, patch

# Mock genai to simulate refusal
def mock_generate_refusal(prompt):
    m = MagicMock()
    m.text = "Please provide the original Vietnamese text so I can rewrite it."
    return m

def mock_generate_success(prompt):
    m = MagicMock()
    m.text = "Translated content successfully."
    return m

def test_rewrite():
    print("--- Test 1: Refusal Pattern ---")
    with patch('google.generativeai.GenerativeModel') as MockModel:
        instance = MockModel.return_value
        instance.generate_content.side_effect = mock_generate_refusal
        
        original = "Original Text Content"
        result = AIService.rewrite_text(original, "dummy_key", "English")
        print(f"Input: {original}")
        print(f"Result: {result}")
        if result == original:
            print("PASS: Returned original text on refusal.")
        else:
            print(f"FAIL: Returned: {result}")

    print("\n--- Test 2: Success Pattern ---")
    with patch('google.generativeai.GenerativeModel') as MockModel:
        instance = MockModel.return_value
        instance.generate_content.side_effect = mock_generate_success
        
        original = "Original Text Content"
        result = AIService.rewrite_text(original, "dummy_key", "English")
        print(f"Input: {original}")
        print(f"Result: {result}")
        if result == "Translated content successfully.":
            print("PASS: Returned rewritten text.")
        else:
            print(f"FAIL: Returned: {result}")

if __name__ == "__main__":
    test_rewrite()
