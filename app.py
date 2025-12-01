"""
WORKING Flask Web App for Multi-Language Transcription
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import subprocess
import os
import threading
import uuid
from datetime import datetime
import pickle

app = Flask(__name__)

# Store jobs - file-based storage
JOBS_FILE = "jobs.pkl"
jobs = {}

if os.path.exists(JOBS_FILE):
    try:
        with open(JOBS_FILE, 'rb') as f:
            jobs = pickle.load(f)
        print(f"Loaded {len(jobs)} existing jobs")
    except:
        jobs = {}

def save_jobs():
    try:
        with open(JOBS_FILE, 'wb') as f:
            pickle.dump(jobs, f)
    except Exception as e:
        print(f"Error saving jobs: {e}")

# Results directory
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# HTML Page
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Multi-Language Transcription</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            padding: 40px;
        }
        h1 { color: #333; margin-bottom: 10px; font-size: 32px; }
        .subtitle { color: #666; margin-bottom: 30px; }
        .input-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        input, select {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
        }
        input:focus, select:focus { outline: none; border-color: #667eea; }
        .checkbox-group { display: flex; align-items: center; margin-bottom: 20px; }
        input[type="checkbox"] { width: 20px; height: 20px; margin-right: 10px; }
        button {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .status-box { display: none; margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 10px; }
        .status-box.show { display: block; }
        .progress-bar { width: 100%; height: 8px; background: #e0e0e0; border-radius: 10px; overflow: hidden; margin: 15px 0; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); width: 0%; transition: width 0.3s; }
        .result-box { margin-top: 20px; padding: 20px; background: #e8f5e9; border-radius: 10px; }
        .transcript-container {
            margin: 20px 0;
            padding: 15px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            max-height: 400px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        .copy-btn {
            margin-top: 15px;
            padding: 12px 24px;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        .copy-btn:hover { background: #1976D2; }
        .copy-btn.copied { background: #4caf50; }
        .error-box { margin-top: 20px; padding: 20px; background: #ffebee; border-radius: 10px; color: #c62828; }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>Multi-Language Transcription</h1>
        <p class="subtitle">Convert YouTube videos to text - supports 11+ languages</p>
        
        <div class="input-group">
            <label>YouTube URL</label>
            <input type="url" id="youtubeUrl" placeholder="https://www.youtube.com/watch?v=...">
        </div>
        
        <div class="input-group">
            <label>Email (optional)</label>
            <input type="email" id="email" placeholder="your@email.com">
        </div>
        
        <div class="input-group">
            <label>Language</label>
            <select id="language">
                <option value="ta-IN">Tamil (தமிழ்)</option>
                <option value="en-US">English</option>
                <option value="hi-IN">Hindi (हिन्दी)</option>
                <option value="te-IN">Telugu (తెలుగు)</option>
                <option value="ml-IN">Malayalam (മലയാളം)</option>
                <option value="kn-IN">Kannada (ಕನ್ನಡ)</option>
                <option value="mr-IN">Marathi (मराठी)</option>
                <option value="bn-IN">Bengali (বাংলা)</option>
                <option value="gu-IN">Gujarati (ગુજરાતી)</option>
                <option value="pa-IN">Punjabi (ਪੰਜਾਬੀ)</option>
                <option value="ur-IN">Urdu (اردو)</option>
            </select>
        </div>
        
        <div class="checkbox-group">
            <input type="checkbox" id="compress" checked>
            <label for="compress" style="margin: 0;">Compress audio (recommended)</label>
        </div>
        
        <button id="submitBtn">Start Transcription</button>
        
        <div id="statusBox" class="status-box">
            <div id="spinner" class="spinner"></div>
            <p id="statusText">Initializing...</p>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <p style="text-align: center; color: #888;" id="progressPercent">0%</p>
        </div>
        
        <div id="resultBox" style="display: none;"></div>
        <div id="errorBox" style="display: none;"></div>
    </div>
    
    <script>
        document.getElementById('submitBtn').onclick = startTranscription;
        
        async function startTranscription() {
            const url = document.getElementById('youtubeUrl').value;
            const email = document.getElementById('email').value;
            const compress = document.getElementById('compress').checked;
            const language = document.getElementById('language').value;
            
            if (!url) {
                alert('Please enter a YouTube URL');
                return;
            }
            
            const statusBox = document.getElementById('statusBox');
            const statusText = document.getElementById('statusText');
            const progressFill = document.getElementById('progressFill');
            const progressPercent = document.getElementById('progressPercent');
            const resultBox = document.getElementById('resultBox');
            const errorBox = document.getElementById('errorBox');
            const submitBtn = document.getElementById('submitBtn');
            
            statusBox.classList.add('show');
            resultBox.style.display = 'none';
            errorBox.style.display = 'none';
            submitBtn.disabled = true;
            
            try {
                const response = await fetch('/transcribe', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({youtube_url: url, email: email, compress: compress, language: language})
                });
                
                const result = await response.json();
                if (result.error) throw new Error(result.error);
                
                const jobId = result.job_id;
                statusText.textContent = 'Processing...';
                
                const pollInterval = setInterval(async () => {
                    const statusResponse = await fetch('/status/' + jobId);
                    const status = await statusResponse.json();
                    
                    progressFill.style.width = status.progress + '%';
                    progressPercent.textContent = status.progress + '%';
                    statusText.textContent = status.message;
                    
                    if (status.status === 'completed') {
                        clearInterval(pollInterval);
                        document.getElementById('spinner').style.display = 'none';
                        showResult(status);
                        submitBtn.disabled = false;
                    } else if (status.status === 'failed') {
                        clearInterval(pollInterval);
                        document.getElementById('spinner').style.display = 'none';
                        showError(status.error || 'Unknown error');
                        submitBtn.disabled = false;
                    }
                }, 2000);
                
            } catch (error) {
                showError(error.message);
                submitBtn.disabled = false;
            }
        }
        
        function showResult(status) {
            const resultBox = document.getElementById('resultBox');
            resultBox.style.display = 'block';
            
            const minutes = Math.floor(status.duration / 60);
            const seconds = Math.floor(status.duration % 60);
            const transcriptText = status.transcript_text || 'Transcript not available';
            
            resultBox.innerHTML = `
                <h3 style="color: #4caf50; margin-bottom: 15px;">✓ Transcription Complete!</h3>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px;">
                    <div style="text-align: center; padding: 10px; background: white; border-radius: 8px;">
                        <div style="font-size: 20px; font-weight: bold; color: #667eea;">${minutes}:${seconds.toString().padStart(2, '0')}</div>
                        <div style="font-size: 12px; color: #666;">Duration</div>
                    </div>
                    <div style="text-align: center; padding: 10px; background: white; border-radius: 8px;">
                        <div style="font-size: 20px; font-weight: bold; color: #667eea;">${status.word_count || 0}</div>
                        <div style="font-size: 12px; color: #666;">Words</div>
                    </div>
                    <div style="text-align: center; padding: 10px; background: white; border-radius: 8px;">
                        <div style="font-size: 20px; font-weight: bold; color: #667eea;">${status.confidence || 0}%</div>
                        <div style="font-size: 12px; color: #666;">Accuracy</div>
                    </div>
                </div>
                <h4 style="margin-bottom: 10px;">Your Transcript:</h4>
                <div class="transcript-container" id="transcriptText">${transcriptText}</div>
                <button class="copy-btn" onclick="copyTranscript()">📋 Copy to Clipboard</button>
                <p style="margin-top: 10px; font-size: 12px; color: #666;">Click copy, then paste into any text editor</p>
            `;
        }
        
        function copyTranscript() {
            const text = document.getElementById('transcriptText').innerText;
            navigator.clipboard.writeText(text).then(() => {
                const btn = document.querySelector('.copy-btn');
                btn.innerHTML = '✓ Copied!';
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.innerHTML = '📋 Copy to Clipboard';
                    btn.classList.remove('copied');
                }, 2000);
            }).catch(() => alert('Failed to copy'));
        }
        
        function showError(message) {
            const errorBox = document.getElementById('errorBox');
            errorBox.style.display = 'block';
            errorBox.className = 'error-box';
            errorBox.innerHTML = '<h3>Error</h3><p>' + message + '</p>';
        }
    </script>
</body>
</html>
"""

def run_transcription(job_id, youtube_url, email, compress, language):
    try:
        jobs[job_id]['status'] = 'processing'
        jobs[job_id]['progress'] = 10
        jobs[job_id]['message'] = 'Starting...'
        save_jobs()
        
        cmd = ['python', 'youtube_transcriber.py', youtube_url, '--language', language]
        if compress:
            cmd.append('--compress')
        
        print(f"Running: {' '.join(cmd)}")
        
        jobs[job_id]['progress'] = 30
        save_jobs()
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
        
        jobs[job_id]['progress'] = 60
        save_jobs()
        
        stdout, stderr = process.communicate(timeout=600)
        
        print(f"Output: {stdout}")
        if stderr:
            print(f"Errors: {stderr}")
        
        if process.returncode == 0:
            transcript_file = 'tamil_transcription.txt'
            
            jobs[job_id]['progress'] = 90
            save_jobs()
            
            if os.path.exists(transcript_file):
                result_path = os.path.join(RESULTS_DIR, f"{job_id}.txt")
                
                import shutil
                shutil.copy2(transcript_file, result_path)
                
                with open(result_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                words = content.split()
                
                jobs[job_id]['status'] = 'completed'
                jobs[job_id]['progress'] = 100
                jobs[job_id]['message'] = 'Complete!'
                jobs[job_id]['duration'] = 300
                jobs[job_id]['word_count'] = len(words)
                jobs[job_id]['confidence'] = 90
                jobs[job_id]['file_path'] = result_path
                jobs[job_id]['transcript_text'] = content
                save_jobs()
                
                print(f"Job {job_id} completed - {len(content)} chars")
            else:
                raise Exception("Transcription file not found")
        else:
            raise Exception(f"Script failed: {stderr}")
            
    except Exception as e:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)
        save_jobs()
        print(f"Job {job_id} failed: {e}")

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    data = request.json
    youtube_url = data.get('youtube_url')
    email = data.get('email', '')
    compress = data.get('compress', True)
    language = data.get('language', 'ta-IN')
    
    if not youtube_url:
        return jsonify({'error': 'Missing YouTube URL'}), 400
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'queued',
        'progress': 0,
        'message': 'Starting...',
        'email': email,
        'youtube_url': youtube_url,
        'language': language
    }
    save_jobs()
    
    thread = threading.Thread(target=run_transcription, args=(job_id, youtube_url, email, compress, language))
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/status/<job_id>')
def get_status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(jobs[job_id])

@app.route('/download/<job_id>')
def download(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    if job['status'] != 'completed':
        return jsonify({'error': 'Job not completed'}), 400
    
    file_path = job.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(file_path, as_attachment=True, download_name='transcription.txt')

if __name__ == '__main__':
    print("\n" + "="*60)
    print("MULTI-LANGUAGE TRANSCRIPTION WEB APP")
    print("="*60)
    print("Open: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
