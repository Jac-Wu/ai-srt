from deep_translator import GoogleTranslator, DeeplTranslator
from typing import List, Dict
from tqdm import tqdm
import time
import sys

class SubtitleTranslator:
    def __init__(self, target_lang: str = 'en', provider: str = 'google', api_key: str = None):
        self.target_lang = target_lang
        self.provider = provider
        
        if provider == 'google':
            self.translator = GoogleTranslator(source='auto', target=target_lang)
        elif provider == 'deepl':
            if not api_key:
                raise ValueError("DeepL API key is required.")
            self.translator = DeeplTranslator(api_key=api_key, source='auto', target=target_lang, use_free_api=True)
        else:
            raise ValueError(f"Provider {provider} not yet implemented in this wrapper.")

    def translate_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Translate the 'text' field of each segment.
        Returns a NEW list of segments with translated text.
        """
        print(f"🌍 Translating {len(segments)} segments to '{self.target_lang}' using {self.provider}...")
        
        translated_segments = []
        
        # Batching isn't natively supported by basic free API wrappers robustly,
        # so we iterate. For a production app, we'd use paid API batch endpoints.
        for seg in tqdm(segments, desc="Translating", unit="seg"):
            original_text = seg['text']
            
            try:
                # Basic retry logic for free iterfaces
                translated_text = self._translate_with_retry(original_text)
            except Exception as e:
                print(f"\n⚠️ Translation failed for segment: '{original_text}'. Keeping original.", file=sys.stderr)
                translated_text = original_text
            
            new_seg = seg.copy()
            new_seg['text'] = translated_text
            translated_segments.append(new_seg)
            
            # Gentle rate limiting
            time.sleep(0.1)
            
        return translated_segments

    def _translate_with_retry(self, text: str, retries: int = 3) -> str:
        if not text.strip():
            return ""
            
        for attempt in range(retries):
            try:
                return self.translator.translate(text)
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(1) # Backoff
