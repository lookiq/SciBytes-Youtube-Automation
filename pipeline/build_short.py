import os
import json
import asyncio
import subprocess
import requests
import edge_tts

DATABASE_FILE = 'pipeline/topics_database.json'
OUTPUT_DIR = 'output'
VOICE = 'en-US-ChristopherNeural'

def get_next_topic():
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        topics = json.load(f)
    for topic in topics:
        if not topic.get('used', False):
            return topic
    for topic in topics:
        topic['used'] = False
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(topics, f, indent=2)
    return topics[0]

def download_footage(url, dest_path):
    print(f'Downloading real footage from: {url}')
    res = requests.get(url, stream=True, timeout=60)
    res.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
    print(f'Footage saved to: {dest_path}')

async def generate_voice(text, dest_path):
    print('Generating Christopher neural voice...')
    communicate = edge_tts.Communicate(text, VOICE, rate='+4%')
    await communicate.save(dest_path)
    print(f'Voice saved to: {dest_path}')

def get_media_duration(file_path):
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
    out = subprocess.check_output(cmd, shell=True, text=True).strip()
    return float(out)

def render_short(topic, footage_path, audio_path, output_path):
    duration = get_media_duration(audio_path)
    print(f'Voice duration: {duration:.2f}s')

    top_header = topic.get('top_header', 'SCIBYTES DAILY').replace("'", "\\'")
    sub_header = topic.get('sub_header', topic['title'].split('#')[0].strip()).replace("'", "\\'")

    subtitle_filters = []
    for sub in topic.get('subtitles', []):
        start = sub['start']
        end = min(sub['end'], duration)
        if start >= duration:
            continue
        text = sub['text'].replace("'", "\\'")
        color = sub.get('color', '#FFFFFF')
        boxcolor = sub.get('boxcolor', 'black@0.9')
        f_str = (
            f"drawtext=text='{text}':fontcolor={color}:fontsize=52:"
            f"x=(w-text_w)/2:y=1380:enable='between(t,{start},{end})':"
            f"box=1:boxcolor={boxcolor}:boxborderw=20"
        )
        subtitle_filters.append(f_str)

    subtitles_cmd_part = ', '.join(subtitle_filters)
    if subtitles_cmd_part:
        subtitles_cmd_part = ', ' + subtitles_cmd_part

    filter_complex = (
        f'[0:v]trim=duration={duration},setpts=PTS-STARTPTS,split=2[orig1][orig2]; '
        f'[orig1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:10,eq=brightness=-0.15[bg]; '
        f'[orig2]scale=1080:-1[fg]; '
        f'[bg][fg]overlay=0:(1920-overlay_h)/2[vid]; '
        f'[vid]drawtext=text=\'SCIBYTES\':fontcolor=#FFCC00:fontsize=40:x=(w-text_w)/2:y=170:box=1:boxcolor=black@0.85:boxborderw=14, '
        f'drawtext=text=\'{top_header}\':fontcolor=#AAAAAA:fontsize=32:x=(w-text_w)/2:y=240:box=1:boxcolor=black@0.8:boxborderw=12, '
        f'drawtext=text=\'{sub_header}\':fontcolor=white:fontsize=46:x=(w-text_w)/2:y=310:box=1:boxcolor=black@0.9:boxborderw=16'
        f'{subtitles_cmd_part}[outv]'
    )

    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-stream_loop', '-1',
        '-i', footage_path,
        '-i', audio_path,
        '-filter_complex', filter_complex,
        '-map', '[outv]',
        '-map', '1:a',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '20',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        output_path
    ]

    print('Rendering vertical Short with FFmpeg...')
    subprocess.run(ffmpeg_cmd, check=True)
    print(f'Short rendered successfully: {output_path}')

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs('temp', exist_ok=True)

    topic = get_next_topic()
    print(f'Selected Topic: {topic["title"]}')

    footage_path = os.path.join('temp', f"{topic['id']}_raw.mp4")
    if not os.path.exists(footage_path) or os.path.getsize(footage_path) == 0:
        download_footage(topic['footage_url'], footage_path)

    audio_path = os.path.join('temp', f"{topic['id']}_voice.mp3")
    asyncio.run(generate_voice(topic['script'], audio_path))

    output_video = os.path.join(OUTPUT_DIR, 'scibytes_short_latest.mp4')
    render_short(topic, footage_path, audio_path, output_video)

    metadata = {
        'id': topic['id'],
        'title': topic['title'],
        'description': (
            f"{topic['script']}\n\n"
            "Subscribe to SciBytes for quick, mind-bending science, space mysteries, and physics facts explained in seconds.\n\n"
            "Copyright Notice:\n"
            "This video contains educational content created under the Fair Use doctrine (Section 107 of the US Copyright Act).\n\n"
            "#SciBytes #Science #Physics #SpaceFacts #Shorts #Astronomy #DidYouKnow"
        ),
        'tags': topic['tags'] + ['SciBytes', 'science', 'physics', 'space facts', 'shorts']
    }

    metadata_file = os.path.join(OUTPUT_DIR, 'metadata.json')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f'Metadata saved: {metadata_file}')
    print('Pipeline build complete!')

if __name__ == '__main__':
    main()
