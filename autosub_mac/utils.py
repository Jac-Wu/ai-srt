import os
from typing import List, Dict

def format_timestamp(seconds: float) -> str:
    """
    Format seconds into SRT timestamp format: HH:MM:SS,mmm
    Example: 12.345 -> 00:00:12,345
    """
    milliseconds = int((seconds - int(seconds)) * 1000)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def write_srt(segments: List[Dict], output_path: str):
    """
    Write segments to an SRT file.
    segments expected format:
    [
        {'start': 0.0, 'end': 2.0, 'text': 'Hello world'},
        ...
    ]
    """
    parent_dir = os.path.dirname(output_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    with open(output_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            start_time = format_timestamp(segment['start'])
            end_time = format_timestamp(segment['end'])
            text = segment['text'].strip()
            
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")

    print(f"✅ SRT file successfully saved to: {output_path}")
