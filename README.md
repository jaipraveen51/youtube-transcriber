# YouTube Multi-Language Transcriber - Flask Web App

A web-based interface for transcribing YouTube videos in multiple Indian languages using Google Cloud Speech-to-Text.

## Features

✅ **11+ Language Support**: Tamil, Hindi, Telugu, Malayalam, Kannada, Marathi, Bengali, Gujarati, Punjabi, Urdu, English
✅ **Beautiful Web Interface**: No command line needed
✅ **Real-time Progress**: See transcription progress live
✅ **Copy to Clipboard**: Easy copying of results
✅ **Speaker Diarization**: Identifies different speakers
✅ **Word-level Timestamps**: Detailed timing information
✅ **Audio Compression**: Option to compress for faster processing

## Setup Instructions

### 1. Install Required Packages

```bash
pip install flask google-cloud-speech google-cloud-storage pytubefix pydub
```

### 2. Install FFmpeg (Required for pydub)

**Windows**:
- Download from: https://ffmpeg.org/download.html
- Add to PATH

**Mac**:
```bash
brew install ffmpeg
```

**Linux**:
```bash
sudo apt install ffmpeg
```

### 3. Google Cloud Setup

1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable these APIs:
   - Cloud Speech-to-Text API
   - Cloud Storage API
4. Create Service Account Key:
   - Go to "IAM & Admin" → "Service Accounts"
   - Create service account
   - Create JSON key
   - Download the credentials.json file
5. Update `youtube_transcriber.py`:
   - Set `GOOGLE_CREDENTIALS_PATH` to your credentials.json path

### 4. Run the Application

```bash
python app.py
```

Then open your browser to: **http://localhost:5000**

## How to Use

1. **Paste YouTube URL** - Copy any YouTube video URL
2. **Select Language** - Choose from 11+ supported languages
3. **Add Email** (Optional) - For notifications
4. **Click Start** - Begin transcription
5. **Wait for Results** - Progress updates in real-time
6. **Copy Transcript** - Click the copy button to get your text

## File Structure

```
.
├── app.py                     # Flask web application
├── youtube_transcriber.py     # Core transcription logic
├── results/                   # Saved transcriptions
├── jobs.pkl                   # Job status (auto-created)
└── README.md                  # This file
```

## Cost Information

- **Free Tier**: 60 minutes/month
- **Pricing**: ~$0.024/minute after free tier
- **Typical Video**: 5-10 minute video = $0.12 - $0.24

## Supported Languages

| Language | Code | Native Name |
|----------|------|-------------|
| Tamil | ta-IN | தமிழ் |
| English | en-US | English |
| Hindi | hi-IN | हिन्दी |
| Telugu | te-IN | తెలుగు |
| Malayalam | ml-IN | മലയാളം |
| Kannada | kn-IN | ಕನ್ನಡ |
| Marathi | mr-IN | मराठी |
| Bengali | bn-IN | বাংলা |
| Gujarati | gu-IN | ગુજરાતી |
| Punjabi | pa-IN | ਪੰਜਾਬੀ |
| Urdu | ur-IN | اردو |

## Troubleshooting

### "No audio stream found"
- Video might be private or age-restricted
- Try a different video

### "Cloud Storage error"
- Make sure Cloud Storage API is enabled
- Check credentials have Storage permissions
- Verify billing is enabled

### "Transcription file not found"
- Check Google Cloud credentials are correct
- Ensure both Speech-to-Text AND Cloud Storage APIs are enabled

### Encoding errors (Windows)
- The app handles this automatically
- If issues persist, use WSL or Linux

## Advanced Usage

### Command Line (without web interface)

```bash
python youtube_transcriber.py <youtube_url> --language ta-IN --compress
```

### Adding More Languages

Edit the dropdown in `app.py` HTML section:
```html
<option value="LANG-CODE">Language Name</option>
```

## Tips for Best Results

1. ✅ **Use compression** for videos longer than 5 minutes
2. ✅ **Clear audio** gives better accuracy
3. ✅ **Avoid background music** when possible
4. ✅ **Check language selection** matches video language

## Next Steps / Future Features

Ideas for improvement:
- [ ] Subtitle (.srt) file generation
- [ ] Translation feature
- [ ] Batch processing multiple URLs
- [ ] Audio file upload (not just YouTube)
- [ ] Export to PDF/DOCX
- [ ] Email notifications
- [ ] User accounts
- [ ] API endpoint

## Support

For issues:
1. Check console logs in terminal
2. Verify Google Cloud setup
3. Test with a short (1-2 min) video first
4. Check API quotas in Google Cloud Console

## License

MIT License - Free to use and modify

---

Built with ❤️ using Flask + Google Cloud Speech-to-Text
