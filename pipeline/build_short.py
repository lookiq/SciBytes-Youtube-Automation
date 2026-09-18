import os
import json
import asyncio
import subprocess
import requests
import edge_tts

TOPICS_FILE = os.path.join(os.path.dirname(__file__), 'topics_database.json')
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output'))
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def synthesize_voice(script_text, output_audio_path):
    print(f"Synthesizing voice: {output_audio_path}...")
    communicate = edge_tts.Communicate(script_text, 'en-US-ChristopherNeural', rate='+4%')
    await communicate.save(output_audio_path)
    print("Voice synthesized successfully.")

def download_footage(url, output_path):
    if os.path.exists(output_path) and os.path.getsize(output_path) > 100000:
        print(f"Footage already cached: {output_path}")
        return
    print(f"Downloading footage from: {url}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, stream=True, headers=headers, timeout=60)
    resp.raise_for_status()
    with open(output_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
    print(f"Footage downloaded: {output_path} ({os.path.getsize(output_path)} bytes)")

def get_audio_duration(audio_path):
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{audio_path}"'
    out = subprocess.check_output(cmd, shell=True, text=True).strip()
    return float(out)

def render_short(topic, audio_path, footage_path, output_video_path):
    duration = get_audio_duration(audio_path)
    print(f"Audio duration: {duration:.2f}s")

    top_header = topic.get('top_header', 'SCIBYTES')
    sub_header = topic.get('sub_header', topic['title'].replace('#Shorts', '').strip())

    sub_filters = []
    for s in topic.get('subtitles', []):
        st = s['start']
        en = min(s['end'], duration)
        txt = s['text'].replace("'", "").replace(":", " -")
        col = s.get('color', '#FFFFFF')
        bcol = s.get('boxcolor', 'black@0.9')
        clause = f"drawtext=text='{txt}':fontcolor={col}:fontsize=52:x=(w-text_w)/2:y=1400:enable='between(t,{st},{en})':box=1:boxcolor={bcol}:boxborderw=20"
        sub_filters.append(clause)

    subtitles_clause = ', '.join(sub_filters)
    if subtitles_clause:
        subtitles_clause = ', ' + subtitles_clause

    filter_complex = (
        f"[0:v]trim=duration={duration},setpts=PTS-STARTPTS,split=2[orig1][orig2]; "
        f"[orig1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:10,eq=brightness=-0.15[bg]; "
        f"[orig2]scale=1080:-1[fg]; "
        f"[bg][fg]overlay=0:(1920-overlay_h)/2[vid]; "
        f"[vid]drawtext=text='{top_header}':fontcolor=#FFCC00:fontsize=40:x=(w-text_w)/2:y=170:box=1:boxcolor=black@0.85:boxborderw=14, "
        f"drawtext=text='{sub_header}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=270:box=1:boxcolor=black@0.9:boxborderw=18"
        f"{subtitles_clause}[outv]"
    )

    ffmpeg_cmd = (
        f'ffmpeg -y -stream_loop -1 -i "{footage_path}" -i "{audio_path}" '
        f'-filter_complex "{filter_complex}" '
        f'-map "[outv]" -map 1:a -c:v libx264 -preset fast -crf 20 -c:a aac -b:a 192k -shortest "{output_video_path}"'
    )

    print("Rendering video with FFmpeg...")
    subprocess.run(ffmpeg_cmd, shell=True, check=True)
    print(f"Video rendered successfully: {output_video_path}")

def main():
    with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
        topics = json.load(f)

    selected = None
    for t in topics:
        if not t.get('used', False):
            selected = t
            break

    if not selected:
        print("All topics used, recycling topics from beginning...")
        for t in topics:
            t['used'] = False
        selected = topics[0]

    print(f"Selected topic: {selected['id']} - {selected['title']}")

    audio_path = os.path.join(OUTPUT_DIR, f"{selected['id']}_voice.mp3")
    footage_path = os.path.join(OUTPUT_DIR, f"{selected['id']}_raw.mp4")
    output_video_path = os.path.join(OUTPUT_DIR, "scibytes_short_latest.mp4")

    asyncio.run(synthesize_voice(selected['script'], audio_path))
    download_footage(selected['footage_url'], footage_path)
    render_short(selected, audio_path, footage_path, output_video_path)

    metadata = {
        'id': selected['id'],
        'title': selected['title'],
        'description': f"{selected['script']}\n\nSubscribe to SciBytes for daily science: https://www.youtube.com/@SciBytesDaily\n\n#SciBytes #Science #Physics #Shorts",
        'tags': selected.get('tags', ['SciBytes', 'science', 'physics', 'shorts']),
        'video_file': output_video_path
    }
    meta_path = os.path.join(OUTPUT_DIR, 'metadata.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f"Metadata saved to: {meta_path}")

if __name__ == '__main__':
    main()
