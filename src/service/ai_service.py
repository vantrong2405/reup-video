import os
import google.generativeai as genai
from pathlib import Path

# Constants
GEMINI_MODEL = 'gemini-pro'
DEFAULT_TARGET_LANGUAGE = "Vietnamese"

class AIService:
    @staticmethod
    def dbg_print(msg):
        print(f"[AIService] {msg}")

    @staticmethod
    def rewrite_text(text_content, api_key, target_language=DEFAULT_TARGET_LANGUAGE):
        if not text_content or not text_content.strip():
            return text_content
            
        if not api_key:
            print("Warning: No Gemini API Key provided for rewriting.")
            return text_content
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = (
            f"Please rewrite the following text into {target_language}. "
            f"Keep the meaning and tone. Return ONLY the translated text.\n\n"
            f"Text: {text_content}"
        )
        
        try:
            response = model.generate_content(prompt)
            if response.text:
                cleaned = response.text.replace("Please provide the original Vietnamese text", "").strip()
                return cleaned if cleaned else text_content
            return text_content
        except Exception as e:
            print(f"Gemini Rewrite Error: {e}")
            return text_content
