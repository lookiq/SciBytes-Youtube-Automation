import subprocess
import os
import re
import json
import tempfile

def clean_vtt_content(vtt_text):
    lines = vtt_text.splitlines()
    cleaned = []
    seen = set()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:') or '-->' in line:
            continue
        # Remove timestamps like <00:00:01.240><c>
        clean_line = re.sub(r'<[^>]+>', '', line)
        clean_line = re.sub(r'\s+', ' ', clean_line).strip()
        if clean_line and clean_line not in seen:
            seen.add(clean_line)
            cleaned.append(clean_line)
    return ' '.join(cleaned)

def extract_transcript_from_url(youtube_url):
    print(f"Extracting transcript and metadata for: {youtube_url}")
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_template = os.path.join(tmp_dir, 'video.%(ext)s')
        
        # 1. Fetch metadata
        meta_cmd = [
            'yt-dlp',
            '--dump-json',
            '--skip-download',
            youtube_url
        ]
        meta_res = subprocess.run(meta_cmd, capture_output=True, text=True, errors='ignore')
        metadata = {}
        if meta_res.returncode != 0:
            err_msg = meta_res.stderr.strip() if meta_res.stderr else "Video is unavailable or link is invalid."
            # Extract readable error line
            readable_lines = [l for l in err_msg.splitlines() if 'ERROR:' in l]
            readable_err = readable_lines[0] if readable_lines else err_msg
            raise ValueError(f"Could not load YouTube video: {readable_err}")

        if meta_res.stdout.strip():
            try:
                metadata = json.loads(meta_res.stdout)
            except Exception:
                pass
                
        title = metadata.get('title')
        if not title:
            raise ValueError(f"Could not retrieve video metadata for: {youtube_url}")
            
        duration = metadata.get('duration', 30)
        
        # 2. Extract Subtitles/Transcript
        sub_cmd = [
            'yt-dlp',
            '--write-auto-sub',
            '--write-sub',
            '--sub-lang', 'en',
            '--skip-download',
            '-o', out_template,
            youtube_url
        ]
        subprocess.run(sub_cmd, capture_output=True, text=True, errors='ignore')
        
        transcript = ""
        for f in os.listdir(tmp_dir):
            if f.endswith('.vtt') or f.endswith('.srt'):
                sub_path = os.path.join(tmp_dir, f)
                with open(sub_path, 'r', encoding='utf-8', errors='ignore') as sub_f:
                    raw_text = sub_f.read()
                    transcript = clean_vtt_content(raw_text)
                    if transcript:
                        break
                        
        if not transcript:
            # Fallback: if no transcript track, use description / title
            desc = metadata.get('description', '')
            if desc and len(desc.strip()) > 40:
                transcript = desc.strip()
                print("Notice: No audio subtitle track found; using video description.")
            else:
                raise ValueError("No spoken transcript found in this video. Please provide a video with spoken English dialogue or commentary.")
            
        print(f"Extracted {len(transcript)} chars from '{title}'")
        return {
            'title': title,
            'duration': duration,
            'transcript': transcript,
            'url': youtube_url
        }

if __name__ == '__main__':
    import sys
    test_url = sys.argv[1] if len(sys.argv) > 1 else 'https://www.youtube.com/shorts/HmlardFioZk'
    res = extract_transcript_from_url(test_url)
    print("Title:", res['title'])
    print("Transcript:", res['transcript'][:200])
