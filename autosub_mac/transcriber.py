from pywhispercpp.model import Model
import sys
import os
from typing import List, Dict
import concurrent.futures

class WhisperTranscriber:
    def __init__(self, model_name: str = "base"):
        """
        Initialize Whisper model.
        
        Args:
            model_name: One of 'tiny', 'base', 'small', 'medium', 'large'
        """
        self.model_name = model_name
        # Note: We won't load the model here for batch processing, 
        # or we might need to handle it carefully.
        # For simple non-batch usage, we load it. 
        # But if we use multi-threading, we might need thread-local models.
        # For simplicity in V1, let's keep the single model for sequential usage,
        # but for batch usage we might instantiate new ones in workers if needed?
        # Actually pywhispercpp/whisper.cpp models are thread-safe for *inference* 
        # if each thread calls transcribe on different data? 
        # C++ usually is, but let's be safe: create one model instance per thread/process to avoid GIL/Lock contention.
        # But loading model is expensive.
        # Let's try sharing the model first. If it crashes, we switch.
        
        print(f"🧠 Loading Whisper model: {model_name}...")
        try:
            # Model will download automatically if not present
            self.model = Model(model_name, print_realtime=False, print_progress=False)
        except Exception as e:
            print(f"❌ Failed to load model '{model_name}': {e}", file=sys.stderr)
            raise e

    def transcribe(self, audio_path: str):
        """
        Transcribe audio file.
        
        Returns:
            List of segments. Each segment is object/dict-like.
            We normalize it to list of dicts: [{'start': float, 'end': float, 'text': str}]
        """
        if not os.path.exists(audio_path):
             raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # print(f"🎙️  Transcribing audio...") # Removing noisy print for batch mode
        try:
            # pywhispercpp transcribe returns segments
            # n_threads defaults to hardware concurrency if not specified
            segments = self.model.transcribe(audio_path, n_threads=6)
            
            # Normalize results
            normalized_segments = []
            for seg in segments:
                text = seg.text
                start_sec = seg.t0 / 100.0
                end_sec = seg.t1 / 100.0
                
                normalized_segments.append({
                    'start': start_sec,
                    'end': end_sec,
                    'text': text
                })
                
            return normalized_segments

        except Exception as e:
            print(f"❌ Transcription failed for {audio_path}: {e}", file=sys.stderr)
            raise e

    def transcribe_batch(self, audio_paths: List[str], max_workers: int = 1, offset_seconds: int = 0) -> List[Dict]:
        """
        Transcribe a list of audio files using the loaded model.
        NOTE: Changed to SEQUENTIAL execution to prevent CoreML/Metal backend crashes.
        The Speedup comes from Metal acceleration, not Python threading.
        """
        print(f"🚀 Starting batch transcription (Sequential)...")
        
        all_segments = []
        
        for index, path in enumerate(audio_paths):
            current_offset = index * offset_seconds
            print(f"▶️ Processing chunk {index+1}/{len(audio_paths)}...")
            try:
                # Run transcription sequentially
                segs = self.transcribe(path)
                
                # Adjust timestamps
                for s in segs:
                    s['start'] += current_offset
                    s['end'] += current_offset
                
                all_segments.extend(segs)
            except Exception as e:
                print(f"❌ Error processing chunk {index}: {e}", file=sys.stderr)
                # Continue to next chunk instead of crashing whole batch
        
        return all_segments
