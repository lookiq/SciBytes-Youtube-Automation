import os
import sys
import json
import shutil
import asyncio
import subprocess
import requests
import urllib.parse
import edge_tts

try:
    from pipeline.seo_engine import generate_seo_metadata
except ImportError:
    from seo_engine import generate_seo_metadata

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

def get_uploaded_history():
    history_titles = set()
    history_footages = set()
    if os.path.exists('upload_history.log'):
        with open('upload_history.log', 'r', encoding='utf-8') as f:
            for line in f:
                if 'Title: ' in line:
                    parts = line.split('Title: ')
                    if len(parts) > 1:
                        title_part = parts[1].split(' | ')[0].strip().lower()
                        history_titles.add(title_part)
                if 'Footage: ' in line:
                    parts = line.split('Footage: ')
                    if len(parts) > 1:
                        footage_part = parts[1].split(' | ')[0].strip()
                        if footage_part and footage_part != 'N/A':
                            history_footages.add(footage_part)
    return history_titles, history_footages

def get_next_topic():
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        topics = json.load(f)

    uploaded_titles, uploaded_footages = get_uploaded_history()

    # Collect all footage URLs that have already been marked used
    used_footage_urls = set(uploaded_footages)
    for topic in topics:
        if topic.get('used', False):
            used_footage_urls.add(topic.get('footage_url'))

    # Pass 1: Check for high-priority event alerts (e.g. EVENT_ALERT, BREAKING, HIGH)
    for topic in topics:
        if not topic.get('used', False) and topic.get('priority') in ['EVENT_ALERT', 'BREAKING', 'HIGH']:
            t_title = topic.get('title', '').strip().lower()
            f_url = topic.get('footage_url')
            if f_url in used_footage_urls:
                continue
            if t_title in uploaded_titles:
                topic['used'] = True
                continue
            print(f"[PRIORITY EVENT ALERT DETECTED] Next topic: {topic.get('title')}")
            return topic

    # Pass 2: Regular sequential scan
    for topic in topics:
        t_title = topic.get('title', '').strip().lower()
        f_url = topic.get('footage_url')

        # Guard 1: Must not already be marked used
        if topic.get('used', False):
            continue

        # Guard 2: Footage URL must NOT match any already-used topic or uploaded footage
        if f_url in used_footage_urls:
            print(f"Skipping topic '{topic.get('title')}' - duplicate footage URL detected: {f_url}")
            continue

        # Guard 3: Title must NOT exist in upload_history.log
        if t_title in uploaded_titles:
            print(f"Skipping topic '{topic.get('title')}' - title already uploaded in history!")
            topic['used'] = True
            continue

        return topic

    # NEVER reset and loop duplicates automatically!
    raise RuntimeError(
        "CRITICAL ERROR: No unused topics with unique footage available in topics_database.json! "
        "All topics or their footage have already been used or uploaded. "
        "Please add new unique topics to pipeline/topics_database.json to prevent duplicate uploads."
    )

def download_footage(url, dest_path):
    norm_url = urllib.parse.quote(urllib.parse.unquote(url), safe=':/?=~')
    print(f'Downloading real footage from: {norm_url}')
    res = requests.get(norm_url, stream=True, timeout=60)
    res.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
    print(f'Footage saved to: {dest_path}')

def format_ass_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int((seconds - int(seconds)) * 100)
    return f"{hours:01d}:{minutes:02d}:{secs:02d}.{centis:02d}"

def create_dynamic_ass_subtitles(sentences, dest_ass_path, words_per_chunk=3):
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,56,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,3,2,40,40,460,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dialogues = []
    for s in sentences:
        start_sec = s['offset'] / 10_000_000
        dur_sec = s['duration'] / 10_000_000
        end_sec = start_sec + dur_sec
        clean_text = s['text'].strip().replace('\\', '').replace('{', '').replace('}', '')
        words = clean_text.split()
        if not words:
            continue
        total_chars = sum(len(w) for w in words)
        curr_time = start_sec
        for i in range(0, len(words), words_per_chunk):
            chunk = words[i:i+words_per_chunk]
            chunk_text = ' '.join(chunk).upper()
            chunk_chars = sum(len(w) for w in chunk)
            chunk_dur = (chunk_chars / total_chars) * dur_sec
            c_start = curr_time
            c_end = min(curr_time + chunk_dur, end_sec)
            dialogues.append(
                f"Dialogue: 0,{format_ass_time(c_start)},{format_ass_time(c_end)},Default,,0,0,0,,{chunk_text}"
            )
            curr_time = c_end

    with open(dest_ass_path, 'w', encoding='utf-8') as f:
        f.write(header + "\n".join(dialogues) + "\n")

async def generate_voice(text, dest_audio_path, dest_ass_path=None):
    print('Generating Christopher neural voice and verbatim timestamps...')
    communicate = edge_tts.Communicate(text, VOICE, rate='+4%')
    audio_bytes = bytearray()
    sentences = []
    async for chunk in communicate.stream():
        if chunk['type'] == 'audio':
            audio_bytes.extend(chunk['data'])
        elif chunk['type'] == 'SentenceBoundary':
            sentences.append(chunk)

    with open(dest_audio_path, 'wb') as f:
        f.write(audio_bytes)
    print(f'Voice saved to: {dest_audio_path}')

    if dest_ass_path and sentences:
        create_dynamic_ass_subtitles(sentences, dest_ass_path)
        print(f'Verbatim ASS subtitles saved to: {dest_ass_path}')

def get_media_duration(file_path):
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
    out = subprocess.check_output(cmd, shell=True, text=True).strip()
    return float(out)

def has_audio_stream(file_path):
    try:
        cmd = ['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', file_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return bool(res.stdout.strip())
    except Exception:
        return False

def get_bright_start_offset(footage_path, base_offset=0.0):
    import re
    current = float(base_offset)
    for step in range(15):
        t = current + (step * 2.0)
        try:
            cmd = ['ffmpeg', '-ss', str(t), '-i', footage_path, '-vframes', '1', '-vf', 'signalstats', '-f', 'null', '-']
            res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, timeout=10)
            m = re.search(r'YAVG=([0-9\.]+)', res.stderr)
            if m:
                luma = float(m.group(1))
                if luma > 18.0:
                    print(f'Detected vibrant visual start at {t:.1f}s (Luma: {luma:.1f})')
                    return t
        except Exception as e:
            print(f'Notice in bright start offset: {e}')
            break
    return current

def render_short(topic, footage_path, audio_path, output_path, ass_path=None):
    duration = get_media_duration(audio_path)
    print(f'Voice duration: {duration:.2f}s')

    base_offset = topic.get('start_offset', 0.0)
    start_offset = get_bright_start_offset(footage_path, base_offset)
    print(f'Using verified footage start offset: {start_offset:.2f}s')

    font_file = get_font_file()
    font_opt = f"fontfile='{font_file}':" if font_file else ""

    top_header = topic.get('top_header', 'SCIBYTES DAILY').replace("'", "’").replace(':', ' - ').replace(',', '')
    sub_header = topic.get('sub_header', topic['title'].split('#')[0].strip()).replace("'", "’").replace(':', ' - ').replace(',', '')

    framing_mode = topic.get('framing_mode', 'fullscreen')
    print(f'Framing mode: {framing_mode}')

    sub_filter = ""
    if ass_path and os.path.exists(ass_path):
        rel_ass = os.path.relpath(ass_path).replace('\\', '/')
        sub_filter = f",ass={rel_ass}"
    else:
        subtitle_filters = []
        for sub in topic.get('subtitles', []):
            start = sub['start']
            end = min(sub['end'], duration)
            if start >= duration:
                continue
            text = sub['text'].replace("'", "’").replace(':', ' - ').replace(',', '')
            color = sub.get('color', '#FFEA00')
            f_str = (
                f"drawtext={font_opt}text='{text}':fontcolor={color}:fontsize=54:"
                f"x=(w-text_w)/2:y=1380:enable='between(t,{start},{end})':"
                f"borderw=6:bordercolor=black:shadowcolor=black@0.95:shadowx=4:shadowy=4"
            )
            subtitle_filters.append(f_str)
        if subtitle_filters:
            sub_filter = ', ' + ', '.join(subtitle_filters)

    if framing_mode == 'smart_canvas':
        filter_complex = (
            f"[0:v]trim=duration={duration},setpts=PTS-STARTPTS,split=2[bg_raw][fg_raw];"
            f"[bg_raw]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.25:contrast=1.1[bg];"
            f"[fg_raw]scale=1080:-2,eq=contrast=1.1:saturation=1.2[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[basev];"
            f"[basev]drawtext={font_opt}text='{top_header}':fontcolor=#FFEA00:fontsize=36:x=(w-text_w)/2:y=170:borderw=4:bordercolor=black:shadowcolor=black@0.9:shadowx=2:shadowy=2,"
            f"drawtext={font_opt}text='{sub_header}':fontcolor=#FFFFFF:fontsize=48:x=(w-text_w)/2:y=240:borderw=5:bordercolor=black:shadowcolor=black@0.9:shadowx=3:shadowy=3,"
            f"drawtext={font_opt}text='SCIBYTES':fontcolor=#888888:fontsize=52:x=(w-text_w)/2:y=1750:shadowcolor=black@0.9:shadowx=2:shadowy=2"
            f"{sub_filter}[outv]"
        )
    else:
        filter_complex = (
            f"[0:v]trim=duration={duration},setpts=PTS-STARTPTS,"
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"eq=contrast=1.12:saturation=1.22:brightness=0.01,"
            f"drawtext={font_opt}text='SCIBYTES':fontcolor=#888888:fontsize=52:x=(w-text_w)/2:y=1750:shadowcolor=black@0.9:shadowx=2:shadowy=2,"
            f"drawtext={font_opt}text='{top_header}':fontcolor=#FFEA00:fontsize=36:x=(w-text_w)/2:y=170:borderw=4:bordercolor=black:shadowcolor=black@0.9:shadowx=2:shadowy=2,"
            f"drawtext={font_opt}text='{sub_header}':fontcolor=#FFFFFF:fontsize=48:x=(w-text_w)/2:y=240:borderw=5:bordercolor=black:shadowcolor=black@0.9:shadowx=3:shadowy=3"
            f"{sub_filter}[outv]"
        )

    has_audio = has_audio_stream(footage_path)
    if has_audio:
        filter_complex += f";[0:a]volume=0.18[foot_a];[1:a]volume=1.0[voice_a];[voice_a][foot_a]amix=inputs=2:duration=first[outa]"
        audio_maps = ['-map', '[outa]']
    else:
        audio_maps = ['-map', '1:a']

    safe_title = topic.get('title', 'SciBytes Short').replace('"', '').replace("'", "")
    safe_comment = topic.get('sub_header', 'SciBytes Science Facts').replace('"', '').replace("'", "")
    container_metadata = [
        '-metadata', f'title={safe_title}',
        '-metadata', 'artist=SciBytes',
        '-metadata', 'album=SciBytes Shorts',
        '-metadata', 'genre=Science & Technology',
        '-metadata', f'comment={safe_comment}'
    ]

    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-ss', str(start_offset),
        '-stream_loop', '-1',
        '-i', footage_path,
        '-i', audio_path,
        '-filter_complex', filter_complex,
        '-map', '[outv]',
        *audio_maps,
        *container_metadata,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        output_path
    ]

    print(f'Rendering {framing_mode} vertical Short with FFmpeg...')
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
                f"drawtext={font_opt}text='{clean_top}':fontcolor=#FFEA00:fontsize=36:x=(w-text_w)/2:y=170:borderw=4:bordercolor=black:shadowcolor=black@0.9:shadowx=2:shadowy=2,"
                f"drawtext={font_opt}text='{clean_sub}':fontcolor=#FFFFFF:fontsize=48:x=(w-text_w)/2:y=240:borderw=5:bordercolor=black:shadowcolor=black@0.9:shadowx=3:shadowy=3,"
                f"drawtext={font_opt}text='{clean_first}':fontcolor=#FF3366:fontsize=54:x=(w-text_w)/2:y=1380:borderw=6:bordercolor=black:shadowcolor=black@0.95:shadowx=4:shadowy=4"
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
    ass_path = os.path.join('temp', f"{topic['id']}_subs.ass")
    asyncio.run(generate_voice(topic['script'], audio_path, ass_path))

    output_video = os.path.join(OUTPUT_DIR, 'scibytes_short_latest.mp4')
    render_short(topic, footage_path, audio_path, output_video, ass_path)

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

    # Generate 100% SEO-Compliant Metadata (VidIQ & TubeBuddy standards)
    seo = generate_seo_metadata(topic)

    # Save offline SEO keyword-rich files
    seo_video_path = os.path.join(OUTPUT_DIR, seo['offline_video_name'])
    shutil.copy2(output_video, seo_video_path)
    print(f"Offline SEO Video saved: {seo_video_path}")

    seo_thumb_path = os.path.join(OUTPUT_DIR, seo['offline_thumb_name'])
    if os.path.exists(thumbnail_path):
        shutil.copy2(thumbnail_path, seo_thumb_path)
        print(f"Offline SEO Thumbnail saved: {seo_thumb_path}")

    metadata = {
        'id': topic['id'],
        'title': seo['title'],
        'description': seo['description'],
        'tags': seo['tags'],
        'offline_video_name': seo['offline_video_name'],
        'offline_thumb_name': seo['offline_thumb_name'],
        'category_id': seo['category_id'],
        'default_language': seo['default_language'],
        'default_audio_language': seo['default_audio_language'],
        'license': seo['license'],
        'footage_url': topic.get('footage_url', ''),
        'seo_audit': {
            'title_length': seo['title_length'],
            'description_length': seo['description_length'],
            'tag_characters': seo['tag_characters'],
            'tag_count': seo['tag_count'],
            'vidiq_score_target': '100/100'
        }
    }

    metadata_file = os.path.join(OUTPUT_DIR, 'metadata.json')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f'SEO Metadata saved: {metadata_file} (Title: {seo["title_length"]} chars | Tags: {seo["tag_characters"]} chars | Desc: {seo["description_length"]} chars)')
    print('Pipeline build complete!')

if __name__ == '__main__':
    main()
