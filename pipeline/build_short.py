import os
import json
import asyncio
import subprocess
import requests
import urllib.parse
import edge_tts

DATABASE_FILE = 'pipeline/topics_database.json'
OUTPUT_DIR = 'output'
VOICE = 'en-US-ChristopherNeural'

def get_font_file():
    # Windows font
    win_font = 'C:/Windows/Fonts/ariblk.ttf'
    if os.path.exists(win_font):
        return 'C\\:/Windows/Fonts/ariblk.ttf'
    # Linux fonts for GitHub Actions runner
    linux_fonts = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
    ]
    for lf in linux_fonts:
        if os.path.exists(lf):
            return lf
    return None

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

    font_file = get_font_file()
    font_opt = f"fontfile='{font_file}':" if font_file else ""

    top_header = topic.get('top_header', 'SCIBYTES DAILY').replace("'", "\\'").replace(':', '\\:')
    sub_header = topic.get('sub_header', topic['title'].split('#')[0].strip()).replace("'", "\\'").replace(':', '\\:')

    subtitle_filters = []
    for sub in topic.get('subtitles', []):
        start = sub['start']
        end = min(sub['end'], duration)
        if start >= duration:
            continue
        text = sub['text'].replace("'", "\\'").replace(':', '\\:')
        color = sub.get('color', '#FFFFFF')
        boxcolor = sub.get('boxcolor', 'black@0.85')
        f_str = (
            f"drawtext={font_opt}text='{text}':fontcolor={color}:fontsize=48:"
            f"x=(w-text_w)/2:y=1400:enable='between(t,{start},{end})':"
            f"box=1:boxcolor={boxcolor}:boxborderw=16"
        )
        subtitle_filters.append(f_str)

    subtitles_cmd_part = ', ' + ', '.join(subtitle_filters) if subtitle_filters else ''

    filter_complex = (
        f"[0:v]trim=duration={duration},setpts=PTS-STARTPTS,"
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"eq=contrast=1.12:saturation=1.22:brightness=0.01,"
        f"drawtext={font_opt}text='SCIBYTES':fontcolor=#555555:fontsize=52:x=(w-text_w)/2:y=1750:shadowcolor=black@0.8:shadowx=2:shadowy=2,"
        f"drawtext={font_opt}text='{top_header}':fontcolor=#FFEA00:fontsize=36:x=(w-text_w)/2:y=170:box=1:boxcolor=black@0.8:boxborderw=14,"
        f"drawtext={font_opt}text='{sub_header}':fontcolor=#FFFFFF:fontsize=48:x=(w-text_w)/2:y=240:box=1:boxcolor=black@0.9:boxborderw=18"
        f"{subtitles_cmd_part}[outv]"
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
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        output_path
    ]

    print('Rendering borderless vertical Short with FFmpeg...')
    subprocess.run(ffmpeg_cmd, check=True)
    print(f'Short rendered successfully: {output_path}')

def generate_photorealistic_thumbnail(topic, output_thumbnail_path):
    print("Generating 100% free photorealistic AI thumbnail...")
    sub_header = topic.get('sub_header', topic['title'].split('#')[0].strip())
    top_header = topic.get('top_header', 'SCIBYTES DAILY')
    first_sub = topic.get('subtitles', [{}])[0].get('text', sub_header)

    base_prompt = topic.get('thumb_prompt')
    if not base_prompt:
        base_prompt = (
            f"raw authentic photograph, National Geographic scientific documentary, "
            f"view of {sub_header} in deep space, NASA satellite telescope photo, "
            f"Hasselblad H6D-100c 85mm lens, photorealistic, 8k, ultra sharp textures, "
            f"natural lighting, zero cgi, zero cartoon, authentic astrophysics"
        )

    encoded = urllib.parse.quote(base_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=flux-realism&nologo=true"

    raw_path = os.path.join('temp', f"{topic['id']}_raw_thumb.jpg")
    try:
        r = requests.get(url, timeout=35)
        if r.status_code == 200 and len(r.content) > 10000:
            with open(raw_path, 'wb') as f:
                f.write(r.content)

            font_file = get_font_file()
            font_opt = f"fontfile='{font_file}':" if font_file else ""

            clean_top = top_header.replace("'", "\\'").replace(':', '\\:')
            clean_sub = sub_header.replace("'", "\\'").replace(':', '\\:')
            clean_first = first_sub.replace("'", "\\'").replace(':', '\\:')

            filter_complex = (
                "crop=in_w:in_h-60:0:0,scale=1080:1920,"
                f"drawtext={font_opt}text='SCIBYTES':fontcolor=#888888:fontsize=52:x=(w-text_w)/2:y=1750:shadowcolor=black@0.9:shadowx=2:shadowy=2,"
                f"drawtext={font_opt}text='{clean_top}':fontcolor=#FFEA00:fontsize=36:x=(w-text_w)/2:y=170:box=1:boxcolor=black@0.8:boxborderw=14,"
                f"drawtext={font_opt}text='{clean_sub}':fontcolor=#FFFFFF:fontsize=48:x=(w-text_w)/2:y=240:box=1:boxcolor=black@0.9:boxborderw=18,"
                f"drawtext={font_opt}text='{clean_first}':fontcolor=#FF3366:fontsize=46:x=(w-text_w)/2:y=1380:box=1:boxcolor=black@0.9:boxborderw=18"
            )
            cmd = ["ffmpeg", "-y", "-i", raw_path, "-vf", filter_complex, "-q:v", "2", output_thumbnail_path]
            subprocess.run(cmd, check=True)
            print(f"Photorealistic AI thumbnail saved: {output_thumbnail_path}")
            return True
    except Exception as e:
        print(f"Notice: AI thumbnail fallback to video hook frame: {e}")
    return False

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

    # Generate photorealistic AI thumbnail with graceful fallback
    thumbnail_path = os.path.join(OUTPUT_DIR, 'thumbnail.jpg')
    success = generate_photorealistic_thumbnail(topic, thumbnail_path)
    if not success or not os.path.exists(thumbnail_path):
        thumb_cmd = [
            'ffmpeg', '-y',
            '-ss', '00:00:01.5',
            '-i', output_video,
            '-vframes', '1',
            '-q:v', '2',
            thumbnail_path
        ]
        print('Generating fallback high-CTR thumbnail from peak hook frame...')
        subprocess.run(thumb_cmd, check=True)
        print(f'Thumbnail saved: {thumbnail_path}')

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
