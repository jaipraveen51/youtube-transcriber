import os
import sys
from google.cloud import speech_v1p1beta1 as speech
from pydub import AudioSegment
import io
import time

# ============================================
# SET YOUR GOOGLE CREDENTIALS PATH HERE
# ============================================
GOOGLE_CREDENTIALS_PATH = "C:/Users/aryap/Downloads/credentials.json"  # Update this path
# ============================================

def extract_audio(youtube_url, output_path="audio.wav", compress=False):
    """
    Extract audio from YouTube video and convert to WAV format
    Uses yt-dlp for better reliability on cloud servers
    
    Args:
        youtube_url: URL of the YouTube video
        output_path: Path where audio file will be saved
        compress: If True, compress to stay under 10MB
    
    Returns:
        Path to the extracted audio file and duration
    """
    try:
        print(f"[>>] Downloading audio from: {youtube_url}")
        print("This may take a few minutes...")
        
        import yt_dlp
        
        # yt-dlp options for audio download
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'temp_audio.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'extract_audio': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
        }
        
        print("[!] Downloading... please wait...")
        
        # Download with yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            duration = info.get('duration', 0)
            
            # Find the downloaded file
            temp_file = None
            for ext in ['wav', 'm4a', 'webm', 'mp4', 'mp3']:
                potential_file = f'temp_audio.{ext}'
                if os.path.exists(potential_file):
                    temp_file = potential_file
                    break
        
        if not temp_file or not os.path.exists(temp_file):
            raise Exception("Downloaded file not found")
        
        print("[OK] Download complete!")
        print("[!] Converting audio format...")
        
        # Convert to WAV using pydub
        audio = AudioSegment.from_file(temp_file)
        audio = audio.set_channels(1)  # Mono
        
        if compress:
            print("[!] Compressing audio to stay under 10MB...")
            audio = audio.set_frame_rate(8000)  # 8kHz for compression
        else:
            audio = audio.set_frame_rate(16000)  # 16kHz for quality
        
        audio.export(output_path, format="wav")
        
        # Clean up temp files
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        file_size = os.path.getsize(output_path)
        print(f"[OK] Audio extracted to: {output_path}")
        print(f"  Duration: {duration//60}:{duration%60:02d} minutes")
        print(f"  File size: {file_size / (1024*1024):.2f} MB")
        
        return output_path, duration
        
    except Exception as e:
        print(f"[ERR] Error extracting audio: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def transcribe_google_stt(audio_path, language_code="ta-IN"):
    """
    Transcribe audio using Google Speech-to-Text API
    Automatically detects sample rate from audio file
    
    Args:
        audio_path: Path to audio file
        language_code: Language code (ta-IN for Tamil India)
    
    Returns:
        Google Speech-to-Text response
    """
    try:
        print(f"\n{'='*60}")
        print("[>>] Transcribing with Google Cloud Speech-to-Text...")
        print(f"{'='*60}")
        
        # Check file size
        file_size = os.path.getsize(audio_path)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"File size: {file_size_mb:.2f} MB")
        
        # Detect sample rate from audio file
        audio_segment = AudioSegment.from_wav(audio_path)
        sample_rate = audio_segment.frame_rate
        print(f"Detected sample rate: {sample_rate} Hz")
        
        client = speech.SpeechClient()
        
        # Configure recognition settings with detected sample rate
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,  # Use detected rate
            language_code=language_code,
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
            model="latest_long",
            use_enhanced=True,
            enable_speaker_diarization=True,
            diarization_speaker_count=2,
        )
        
        print(f"Language: Tamil (ta-IN)")
        print(f"Model: latest_long (Enhanced)")
        print(f"Features: Speaker diarization, Punctuation, Timestamps")
        
        # Google Cloud Speech has a ~60 second limit for inline audio
        # For anything longer, we MUST use Cloud Storage
        # File size limit is 10MB for inline, but duration is the real constraint
        
        # Always use Cloud Storage for safety (videos are usually > 1 min)
        print(f"\n[!] Using Google Cloud Storage for transcription...")
        print("This is required for videos longer than 1 minute.")
        
        try:
            from google.cloud import storage
            import uuid
            
            # Create storage client
            storage_client = storage.Client()
            
            # Create a unique bucket name using UUID
            unique_id = str(uuid.uuid4())[:8]
            bucket_name = f"speech-transcription-{unique_id}"
            
            try:
                bucket = storage_client.get_bucket(bucket_name)
            except:
                print(f"Creating bucket: {bucket_name}")
                bucket = storage_client.create_bucket(bucket_name, location="us")
            
            # Upload file
            blob_name = f"audio_{int(time.time())}.wav"
            blob = bucket.blob(blob_name)
            
            print(f"[>>] Uploading to Cloud Storage...")
            blob.upload_from_filename(audio_path)
            
            gcs_uri = f"gs://{bucket_name}/{blob_name}"
            print(f"[OK] Uploaded to: {gcs_uri}")
            
            # Use GCS URI for transcription
            audio = speech.RecognitionAudio(uri=gcs_uri)
            
            print("\n[...] Processing transcription...")
            operation = client.long_running_recognize(config=config, audio=audio)
            response = operation.result(timeout=600)
            
            # Clean up
            print("[!] Cleaning up Cloud Storage...")
            blob.delete()
            try:
                bucket.delete()
            except:
                pass
            
        except ImportError:
            print("\n[ERR] google-cloud-storage not installed")
            print("For videos longer than 1 minute, you MUST use Cloud Storage.")
            print("\nInstall with: pip install google-cloud-storage")
            print("Then enable Cloud Storage API in Google Cloud Console")
            sys.exit(1)
        except Exception as storage_error:
            print(f"\n[ERR] Cloud Storage error: {storage_error}")
            print("\nMake sure:")
            print("1. Cloud Storage API is enabled in Google Cloud Console")
            print("2. Your credentials have Cloud Storage permissions")
            print("3. pip install google-cloud-storage")
            sys.exit(1)
        
        print(f"[OK] Transcription completed successfully!")
        
        return response
        
    except Exception as e:
        print(f"[ERR] Error transcribing audio: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure packages are installed:")
        print("   pip install google-cloud-speech google-cloud-storage yt-dlp pydub")
        print("2. For files over 10MB, Cloud Storage is required")
        print("3. Enable both APIs: Speech-to-Text AND Cloud Storage")
        print("4. Make sure you have billing enabled")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def save_transcription(response, output_file="tamil_transcription.txt"):
    """
    Save Google STT transcription to file with detailed information
    
    Args:
        response: Google Speech-to-Text response
        output_file: Output file path
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("="*60 + "\n")
            f.write("TAMIL TRANSCRIPTION - Google Cloud Speech-to-Text\n")
            f.write("="*60 + "\n\n")
            
            # Collect full transcript
            full_transcript = ""
            for result in response.results:
                full_transcript += result.alternatives[0].transcript + " "
            
            # Write full transcription
            f.write("="*60 + "\n")
            f.write("FULL TRANSCRIPTION:\n")
            f.write("="*60 + "\n\n")
            f.write(full_transcript.strip())
            f.write("\n\n")
            
            # Write detailed results with confidence and timing
            f.write("="*60 + "\n")
            f.write("DETAILED SEGMENTS:\n")
            f.write("="*60 + "\n\n")
            
            for i, result in enumerate(response.results):
                alternative = result.alternatives[0]
                
                f.write(f"\n--- Segment {i+1} ---\n")
                f.write(f"Transcript: {alternative.transcript}\n")
                f.write(f"Confidence: {alternative.confidence:.2%}\n")
                
                # Write word-level timestamps if available
                if hasattr(alternative, 'words') and alternative.words:
                    f.write("\nWord timings:\n")
                    for word_info in alternative.words:
                        word = word_info.word
                        start_time = word_info.start_time.total_seconds()
                        end_time = word_info.end_time.total_seconds()
                        
                        # Check for speaker tag
                        speaker = ""
                        if hasattr(word_info, 'speaker_tag'):
                            speaker = f" [Speaker {word_info.speaker_tag}]"
                        
                        f.write(f"  [{start_time:>7.2f}s - {end_time:>7.2f}s]: {word}{speaker}\n")
                
                f.write("\n")
        
        print(f"\n[OK] Transcription saved to: {output_file}")
        
        # Calculate average confidence
        confidences = [result.alternatives[0].confidence for result in response.results if result.alternatives[0].confidence > 0]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            print(f"  Average confidence: {avg_confidence:.2%}")
        
        # Print file size
        file_size = os.path.getsize(output_file)
        print(f"  File size: {file_size:,} bytes")
        
    except Exception as e:
        print(f"[ERR] Error saving transcription: {e}")

def display_preview(response):
    """
    Display a preview of the transcription
    """
    try:
        full_text = ""
        for result in response.results:
            full_text += result.alternatives[0].transcript + " "
        
        print("\n" + "="*60)
        print("[PREVIEW] TRANSCRIPTION PREVIEW:")
        print("="*60)
        
        # Show first 500 characters
        preview = full_text.strip()[:500]
        print(preview)
        if len(full_text) > 500:
            print("...")
            print(f"\n(Showing first 500 of {len(full_text)} characters)")
        
        print("="*60)
        
    except Exception as e:
        print(f"Could not display preview: {e}")

def main():
    """
    Main function
    """
    print("\n" + "="*60)
    print("YouTube Tamil Transcriber - Google Cloud Speech-to-Text")
    print("="*60 + "\n")
    
    # Check if URL is provided
    if len(sys.argv) < 2:
        print("Usage: python script.py <youtube_url> [--language LANG] [--compress]")
        print("\nExample:")
        print("  python script.py https://www.youtube.com/watch?v=xxxxx")
        print("  python script.py https://www.youtube.com/watch?v=xxxxx --language en-US")
        print("  python script.py https://www.youtube.com/watch?v=xxxxx --language ta-IN --compress")
        print("\nOptions:")
        print("  --language LANG : Language code (default: ta-IN)")
        print("                    ta-IN (Tamil), en-US (English), hi-IN (Hindi)")
        print("                    te-IN (Telugu), ml-IN (Malayalam), etc.")
        print("  --compress      : Compress audio to stay under 10MB (lower quality)")
        print("\nSetup Required:")
        print("  1. Install: pip install google-cloud-speech google-cloud-storage yt-dlp pydub")
        print("  2. Create Google Cloud project")
        print("  3. Enable Speech-to-Text API AND Cloud Storage API")
        print("  4. Download credentials JSON")
        print("  5. Set GOOGLE_CREDENTIALS_PATH in this script")
        print("\nGoogle Cloud Features:")
        print("  • Excellent accuracy (90-95%)")
        print("  • Speaker diarization")
        print("  • Automatic punctuation")
        print("  • Word-level timestamps")
        print("  • Free tier: 60 minutes/month")
        print("  • Pricing: ~$0.024/minute after free tier")
        print("\n" + "="*60)
        sys.exit(1)
    
    youtube_url = sys.argv[1]
    compress = "--compress" in sys.argv
    
    # Get language from command line arguments
    language_code = "ta-IN"  # Default to Tamil
    if "--language" in sys.argv:
        lang_index = sys.argv.index("--language")
        if lang_index + 1 < len(sys.argv):
            language_code = sys.argv[lang_index + 1]
    
    print(f"Language: {language_code}")
    
    # Set Google credentials
    # First, check for secret file (most secure - Render)
    secret_file_path = "/etc/secrets/credentials.json"
    if os.path.exists(secret_file_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = secret_file_path
        print(f"[OK] Using credentials from secret file")
    # Second, check for JSON string in environment variable (backup method)
    elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        import json
        import tempfile
        credentials_dict = json.loads(credentials_json)
        temp_creds = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(credentials_dict, temp_creds)
        temp_creds.close()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_creds.name
        print(f"[OK] Using credentials from environment variable")
    else:
        # Use local file path
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or GOOGLE_CREDENTIALS_PATH
        
        if credentials_path and credentials_path != "path/to/your/credentials.json":
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            print(f"[OK] Using credentials: {credentials_path}")
        else:
            print("[ERR] ERROR: Google credentials not set!")
            print("\nPlease follow these steps:")
            print("  1. Go to: https://console.cloud.google.com/")
            print("  2. Create a new project")
            print("  3. Enable 'Cloud Speech-to-Text API'")
            print("  4. Create credentials (Service Account Key)")
            print("  5. Download the JSON file")
            print("  6. Edit this script and set GOOGLE_CREDENTIALS_PATH")
            print("\nDetailed guide: https://cloud.google.com/speech-to-text/docs/before-you-begin")
            print("\n" + "="*60)
            sys.exit(1)
    
    # Extract audio from YouTube
    audio_file = "tamil_audio.wav"
    try:
        audio_path, duration = extract_audio(youtube_url, audio_file, compress=compress)
        
        if compress:
            print("\n[!] Note: Audio was compressed. Accuracy may be slightly reduced.")
        
        # Calculate estimated cost
        minutes = duration / 60
        if minutes <= 60:
            cost = 0  # Free tier
        else:
            cost = (minutes - 60) * 0.024
        
        print(f"\n[COST] Estimated cost: ${cost:.3f}")
        if cost == 0:
            print("   (Within free tier: 60 min/month)")
        
    except Exception as e:
        print(f"\n[ERR] Failed to extract audio: {e}")
        sys.exit(1)
    
    # Transcribe audio
    if os.path.exists(audio_file):
        try:
            response = transcribe_google_stt(audio_file, language_code=language_code)
            
            # Display preview
            display_preview(response)
            
            # Save complete transcription
            save_transcription(response, "tamil_transcription.txt")
            
            print("\n" + "="*60)
            print("[SUCCESS] COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"[FILE] Audio file: {audio_file}")
            print(f"[FILE] Transcription file: tamil_transcription.txt")
            print(f"[TIME] Duration: {duration//60}:{duration%60:02d} minutes")
            print(f"[COST] Estimated cost: ${cost:.3f}")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n[ERR] Transcription failed: {e}")
            sys.exit(1)
    else:
        print(f"[ERR] Error: Audio file not found")
        sys.exit(1)

if __name__ == "__main__":
    main()
