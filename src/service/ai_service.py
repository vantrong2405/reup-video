import os
import whisper
import google.generativeai as genai
import asyncio
from edge_tts import Communicate
from pathlib import Path

class AIService:
    @staticmethod
    def transcribe_audio(audio_path, model_name="base"):
        model = whisper.load_model(model_name)
        result = model.transcribe(str(audio_path))
        return result["text"]

    @staticmethod
    def rewrite_text(text, api_key, target_language=None):
        genai.configure(api_key=api_key)
        
        lang_instruction = ""
        if target_language and target_language.lower() != "original":
             lang_instruction = f" Và dịch nội dung sang ngôn ngữ: {target_language}."

        prompt = (
            f"Hãy viết lại đoạn văn bản sau đây.{lang_instruction} "
            f"Yêu cầu: "
            f"1. Giữ nguyên ý nghĩa cốt lõi. "
            f"2. Thay đổi cách diễn đạt cho tự nhiên, giống văn nói. "
            f"3. TUYỆT ĐỐI CHỈ TRẢ VỀ VĂN BẢN ĐÍCH (ĐÃ DỊCH/VIẾT LẠI). Không bao gồm bất kỳ lời dẫn, giải thích, hay tiêu đề nào như 'Bản dịch:', 'Viết lại:'. "
            f"4. Nếu có yêu cầu dịch, hãy đảm bảo đầu ra là hoàn toàn bằng ngôn ngữ đích ({target_language}). "
            f"Nội dung gốc: {text}"
        )

        if not text or len(text.strip()) < 5:
            print("Warning: Input text for rewrite is too short. Returning original.")
            return text

        try:
             model = genai.GenerativeModel('gemini-2.0-flash')
             response = model.generate_content(prompt)
             result = response.text.strip()
             
             # Check for common refusal patterns
             lower_res = result.lower()
             if "please provide" in lower_res or "i cannot" in lower_res or "need the original" in lower_res:
                 print(f"Warning: Gemini refused to rewrite. Output: {result}")
                 return text # Fallback to original
             
             return result
        except Exception as e:
             print(f"Gemini rewrite failed: {e}")
             return text # Fallback to original

    @staticmethod
    def transcribe_audio_to_srt(audio_path, output_srt_path, model_name="base"):
        model = whisper.load_model(model_name)
        result = model.transcribe(str(audio_path))
        segments = result["segments"]
        
        def format_timestamp(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = seconds % 60
            milliseconds = int((seconds - int(seconds)) * 1000)
            return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

        with open(output_srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments):
                start = format_timestamp(segment["start"])
                end = format_timestamp(segment["end"])
                text = segment["text"].strip()
                f.write(f"{i + 1}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")
        
        return output_srt_path

    @staticmethod
    async def text_to_speech(text, output_path, voice="vi-VN-HoaiMyNeural"):
        communicate = Communicate(text, voice)
        await communicate.save(str(output_path))
        return output_path

    @staticmethod
    def run_openai_tts(text, output_path, api_key, voice="alloy"):
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        response.stream_to_file(str(output_path))
        return output_path

    @staticmethod
    def run_tts_sync(text, output_path, voice=None, openai_key=None, language="vi"):
        if openai_key:
            try:
                print(f"DEBUG: Using OpenAI TTS (Voice: {voice or 'alloy'})...")
                return AIService.run_openai_tts(text, output_path, openai_key, voice=voice or "alloy")
            except Exception as e:
                print(f"OpenAI TTS failed: {e}. Falling back to Edge TTS...")

        try:
            # Default Edge TTS voice if not set. 
            # Note: If language changed to English but voice is still vi-VN, it might sound bad.
            # Ideally user should provide correct voice.
            edge_voice = voice if voice and "Neural" in voice else "vi-VN-HoaiMyNeural"
            print(f"DEBUG: Using Edge TTS (Voice: {edge_voice})...")
            asyncio.run(AIService.text_to_speech(text, output_path, edge_voice))
            return output_path
        except Exception as e:
            # Map full language name to code for gTTS (e.g. English -> en)
            lang_code = "vi"
            if language:
                l = language.lower()
                if "english" in l or "anh" in l: lang_code = "en"
                elif "french" in l or "pháp" in l: lang_code = "fr"
                elif "chinese" in l or "trung" in l: lang_code = "zh-cn"
                elif "japanese" in l or "nhật" in l: lang_code = "ja"
                elif "korean" in l or "hàn" in l: lang_code = "ko"
            
            print(f"Edge TTS failed: {e}. Falling back to gTTS (Lang: {lang_code})...")
            from gtts import gTTS
            tts = gTTS(text, lang=lang_code)
            tts.save(str(output_path))
        return output_path
