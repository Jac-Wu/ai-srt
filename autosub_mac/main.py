import argparse
import os
import sys
from .audio import extract_audio, split_audio
from .transcriber import WhisperTranscriber
from .translator import SubtitleTranslator
from .utils import write_srt

def main():
    parser = argparse.ArgumentParser(description="Auto-Subtitle Generator for macOS (WhisperCPP)")
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("--model", default="base", help="Whisper model size (tiny, base, small, medium, large)")
    parser.add_argument("--lang", default="en", help="Target language for translation. Defaults to 'en'.")
    parser.add_argument("--provider", default="google", choices=["google", "deepl"], help="Translation provider. Defaults to 'google'.")
    parser.add_argument("--api-key", help="API Key for translation provider (required for DeepL).")
    parser.add_argument("--output", help="Output SRT file path.")
    parser.add_argument("--no-translate", action="store_true", help="Skip translation.")
    
    # New args
    parser.add_argument("--segment-duration", type=int, default=0, help="Split audio into chunks of N seconds. 0 (default) means no splitting.")
    parser.add_argument("--threads", type=int, default=1, help="Number of parallel threads for transcription. Defaults to 1. Only effective if segment-duration > 0.")
    
    args = parser.parse_args()

    video_path = args.video_path
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file '{video_path}' does not exist.")
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # 1. Extract Audio
    audio_files_to_process = []
    main_audio_file = f"temp_{base_name}.wav"
    try:
        extract_audio(video_path, main_audio_file)
    except Exception:
        sys.exit(1)

    # 2. Split Audio (Optional)
    temp_chunks = []
    if args.segment_duration > 0:
        try:
            temp_chunks = split_audio(main_audio_file, args.segment_duration)
            audio_files_to_process = temp_chunks
        except Exception:
             # Fallback to main audio if split fails?
             print("⚠️ Splitting failed, falling back to single file processing.")
             audio_files_to_process = [main_audio_file]
    else:
        audio_files_to_process = [main_audio_file]

    # 3. Transcribe
    try:
        transcriber = WhisperTranscriber(model_name=args.model)
        
        if len(audio_files_to_process) > 1:
            print(f"🏎️  Running parallel transcription on {len(audio_files_to_process)} chunks with {args.threads} threads...")
            segments = transcriber.transcribe_batch(
                audio_files_to_process, 
                max_workers=args.threads, 
                offset_seconds=args.segment_duration
            )
        else:
            segments = transcriber.transcribe(audio_files_to_process[0])
            
    except Exception:
        # Cleanup
        if os.path.exists(main_audio_file): os.remove(main_audio_file)
        for f in temp_chunks: 
            if os.path.exists(f): os.remove(f)
        sys.exit(1)

    # 4. Translate (Optional)
    final_segments = segments
    if not args.no_translate:
        try:
            translator = SubtitleTranslator(target_lang=args.lang, provider=args.provider, api_key=args.api_key)
            final_segments = translator.translate_segments(segments)
        except Exception as e:
            print(f"⚠️ Translation failed: {e}. Falling back to original transcription.")

    # 5. Write SRT
    if args.output:
        output_srt = args.output
    else:
        suffix = f".{args.lang}" if not args.no_translate else ""
        output_srt = f"{base_name}{suffix}.srt"
        
    write_srt(final_segments, output_srt)
    
    # Final Cleanup
    if os.path.exists(main_audio_file):
        os.remove(main_audio_file)
    for f in temp_chunks:
        if os.path.exists(f): os.remove(f)
    
    print("✨ Done!")

if __name__ == "__main__":
    main()
