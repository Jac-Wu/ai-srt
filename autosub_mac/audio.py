import ffmpeg
import os
import sys
from typing import List

def extract_audio(video_path: str, output_path: str = "temp_audio.wav") -> str:
    """
    Extract audio from video and convert to 16kHz mono WAV (Whisper friendly format).
    Returns the path to the extracted audio file.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    print(f"🎵 Extracting audio from {os.path.basename(video_path)}...")
    
    try:
        # Whisper expects 16kHz audio, usually mono is fine
        (
            ffmpeg
            .input(video_path)
            .output(output_path, ac=1, ar='16000')
            .overwrite_output()
            .run(quiet=True)
        )
        print(f"✅ Audio extracted to: {output_path}")
        return output_path
    except ffmpeg.Error as e:
        print("❌ FFmpeg error occurred. Please ensure ffmpeg is installed via 'brew install ffmpeg'.", file=sys.stderr)
        print(f"Detail: {e.stderr.decode() if e.stderr else 'Unknown error'}", file=sys.stderr)
        raise e

def split_audio(audio_path: str, segment_duration_sec: int = 600) -> List[str]:
    """
    Split audio file into chunks of segment_duration_sec.
    Returns a list of paths to the split audio files.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    print(f"✂️  Splitting audio into {segment_duration_sec}s chunks...")
    
    # Get duration
    try:
        probe = ffmpeg.probe(audio_path)
        duration = float(probe['format']['duration'])
    except ffmpeg.Error as e:
         print(f"❌ Failed to probe audio duration: {e.stderr.decode() if e.stderr else str(e)}", file=sys.stderr)
         raise e

    output_pattern = f"{os.path.splitext(audio_path)[0]}_%03d.wav"
    output_files = []
    
    # Calculate expected number of chunks
    import math
    num_chunks = math.ceil(duration / segment_duration_sec)
    
    try:
        (
            ffmpeg
            .input(audio_path)
            .output(output_pattern, f='segment', segment_time=segment_duration_sec, c='copy')
            .overwrite_output()
            .run(quiet=True)
        )
        
        # Determine generated filenames
        base = os.path.splitext(audio_path)[0]
        for i in range(num_chunks):
            # ffmpeg segment file naming starts at 0
            # pattern %03d means 000, 001, etc.
            chunk_filename = f"{base}_{i:03d}.wav"
            if os.path.exists(chunk_filename):
                output_files.append(chunk_filename)
        
        print(f"✅ Audio split into {len(output_files)} chunks.")
        return output_files
        
    except ffmpeg.Error as e:
        print(f"❌ Audio splitting failed: {e.stderr.decode() if e.stderr else str(e)}", file=sys.stderr)
        raise e

