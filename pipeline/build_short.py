import os
import sys
import json
import shutil
import asyncio
import subprocess
import requests
import urllib.parse
import re
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

def get_next_topic(exclude_ids=None):
    if exclude_ids is None:
        exclude_ids = set()

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
        if topic.get('id') in exclude_ids:
            continue
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
        if topic.get('id') in exclude_ids:
            continue
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
    p = urllib.parse.urlsplit(url)
    clean_path = urllib.parse.quote(urllib.parse.unquote(p.path))
    norm_url = urllib.parse.urlunsplit((p.scheme or 'https', p.netloc, clean_path, p.query, p.fragment))
    if norm_url.startswith('http://'):
        norm_url = 'https://' + norm_url[7:]
    print(f'Downloading real footage from: {norm_url}')
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    res = requests.get(norm_url, headers=headers, stream=True, timeout=60)
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
Style: CapCut,Arial,62,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,3,2,40,40,430,1

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
        word_objs = []
        for w in words:
            w_dur = (len(w) / total_chars) * dur_sec
            w_start = curr_time
            w_end = min(curr_time + w_dur, end_sec)
            word_objs.append({'word': w, 'start': w_start, 'end': w_end})
            curr_time = w_end

        for i in range(0, len(word_objs), words_per_chunk):
            chunk = word_objs[i:i+words_per_chunk]
            for active_idx, target_w in enumerate(chunk):
                styled_words = []
                for j, w in enumerate(chunk):
                    w_up = w['word'].upper()
                    if j == active_idx:
                        styled_words.append(r"{\c&H00E6FF&}" + w_up + r"{\c&HFFFFFF&}")
                    else:
                        styled_words.append(w_up)
                line_text = ' '.join(styled_words)
                dialogues.append(
                    f"Dialogue: 0,{format_ass_time(target_w['start'])},{format_ass_time(target_w['end'])},CapCut,,0,0,0,,{line_text}"
                )

    with open(dest_ass_path, 'w', encoding='utf-8') as f:
        f.write(header + "\n".join(dialogues) + "\n")

def create_ass_from_elevenlabs_alignment(alignment, dest_ass_path, words_per_chunk=3):
    chars = alignment.get('characters', [])
    starts = alignment.get('character_start_times_seconds', [])
    ends = alignment.get('character_end_times_seconds', [])

    words = []
    curr = []
    w_start = None
    for i, ch in enumerate(chars):
        s = starts[i]
        e = ends[i]
        if ch.isspace():
            if curr and w_start is not None:
                words.append({'word': ''.join(curr), 'start': w_start, 'end': ends[i-1] if i > 0 else e})
                curr = []
                w_start = None
        else:
            if w_start is None:
                w_start = s
            curr.append(ch)
    if curr and w_start is not None:
        words.append({'word': ''.join(curr), 'start': w_start, 'end': ends[-1]})

    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CapCut,Arial,62,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,3,2,40,40,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dialogues = []
    for i in range(0, len(words), words_per_chunk):
        chunk = words[i:i+words_per_chunk]
        for active_idx, target_w in enumerate(chunk):
            styled_words = []
            for j, w in enumerate(chunk):
                cleaned_word = w['word'].replace('\\', '').replace('{', '').replace('}', '').upper()
                if j == active_idx:
                    styled_words.append(r"{\c&H00E6FF&}" + cleaned_word + r"{\c&HFFFFFF&}")
                else:
                    styled_words.append(cleaned_word)
            line_text = ' '.join(styled_words)
            c_start = target_w['start']
            c_end = target_w['end']
            dialogues.append(
                f"Dialogue: 0,{format_ass_time(c_start)},{format_ass_time(c_end)},CapCut,,0,0,0,,{line_text}"
            )

    with open(dest_ass_path, 'w', encoding='utf-8') as f:
        f.write(header + "\n".join(dialogues) + "\n")

def generate_elevenlabs_voice(text, dest_audio_path, dest_ass_path=None):
    api_key = os.environ.get('ELEVENLABS_API_KEY')
    if not api_key or not api_key.strip():
        raise ValueError("ELEVENLABS_API_KEY is not set.")

    voice_id = os.environ.get('ELEVENLABS_VOICE_ID', 'pNInz6obpgDQGcFmaJgB')  # Default: Adam
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    headers = {
        "xi-api-key": api_key.strip(),
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }

    print(f"Requesting voiceover from ElevenLabs (Voice ID: {voice_id})...")
    res = requests.post(url, headers=headers, json=payload, timeout=45)

    if res.status_code == 401:
        raise PermissionError("ElevenLabs: Invalid API Key (401)")
    elif res.status_code in (402, 429):
        raise ResourceWarning(f"ElevenLabs: Quota exceeded or payment required ({res.status_code})")
    elif res.status_code != 200:
        raise RuntimeError(f"ElevenLabs API error ({res.status_code}): {res.text[:200]}")

    data = res.json()
    audio_base64 = data.get('audio_base64')
    if not audio_base64:
        raise RuntimeError("No audio data returned from ElevenLabs API")

    import base64
    audio_bytes = base64.b64decode(audio_base64)
    with open(dest_audio_path, 'wb') as f:
        f.write(audio_bytes)

    alignment = data.get('alignment', {})
    if dest_ass_path and alignment:
        create_ass_from_elevenlabs_alignment(alignment, dest_ass_path)
        print(f"Dynamic ASS subtitles generated from ElevenLabs timestamps: {dest_ass_path}")

async def generate_edge_voice(text, dest_audio_path, dest_ass_path=None):
    voice_to_use = 'en-US-BrianMultilingualNeural'
    print(f"Generating Free Studio Neural voice ({voice_to_use}) and verbatim timestamps...")
    try:
        communicate = edge_tts.Communicate(text, voice_to_use, rate='+3%')
        audio_bytes = bytearray()
        sentences = []
        async for chunk in communicate.stream():
            if chunk['type'] == 'audio':
                audio_bytes.extend(chunk['data'])
            elif chunk['type'] == 'SentenceBoundary':
                sentences.append(chunk)
    except Exception as e:
        print(f"Notice with primary neural voice ({e}), falling back to ChristopherNeural...")
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
    print(f"Voice saved to: {dest_audio_path}")

    if dest_ass_path and sentences:
        create_dynamic_ass_subtitles(sentences, dest_ass_path)
        print(f"Verbatim ASS subtitles saved to: {dest_ass_path}")

def generate_voice(text, dest_audio_path, dest_ass_path=None):
    eleven_key = os.environ.get('ELEVENLABS_API_KEY')
    if eleven_key and eleven_key.strip():
        try:
            print("Attempting ultra-realistic ElevenLabs voiceover...")
            generate_elevenlabs_voice(text, dest_audio_path, dest_ass_path)
            print("ElevenLabs voiceover generated successfully!")
            return
        except Exception as e:
            print(f"Notice: ElevenLabs unavailable or quota exceeded: {e}")
            print("Seamlessly falling back to Free Studio-Mastered Neural Voice (Edge-TTS)...")

    asyncio.run(generate_edge_voice(text, dest_audio_path, dest_ass_path))

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
            f"[bg_raw]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.35:contrast=1.15[bg];"
            f"[fg_raw]scale=1080:-2,"
            f"scale=w='1080*(1+0.08*t/{duration})':h='-2':eval=frame,"
            f"crop=1080:ih:(in_w-1080)/2:0,"
            f"eq=contrast=1.15:saturation=1.25[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[basev];"
            f"[basev]vignette=angle=0.38,fade=t=in:st=0:d=0.35,"
            f"drawbox=y=0:h=330:color=black@0.40:t=fill,"
            f"drawbox=y=1280:h=640:color=black@0.40:t=fill,"
            f"drawtext={font_opt}text='{top_header}':fontcolor=#FFEA00:fontsize=36:x=(w-text_w)/2:y=170:borderw=4:bordercolor=black:shadowcolor=black@0.9:shadowx=2:shadowy=2,"
            f"drawtext={font_opt}text='{sub_header}':fontcolor=#FFFFFF:fontsize=48:x=(w-text_w)/2:y=240:borderw=5:bordercolor=black:shadowcolor=black@0.9:shadowx=3:shadowy=3,"
            f"drawtext={font_opt}text='SCIBYTES':fontcolor=#888888:fontsize=52:x=(w-text_w)/2:y=1750:shadowcolor=black@0.9:shadowx=2:shadowy=2"
            f"{sub_filter}[outv]"
        )
    else:
        filter_complex = (
            f"[0:v]trim=duration={duration},setpts=PTS-STARTPTS,"
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"scale=w='1080*(1+0.08*t/{duration})':h='1920*(1+0.08*t/{duration})':eval=frame,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
            f"vignette=angle=0.38,fade=t=in:st=0:d=0.35,"
            f"eq=contrast=1.16:saturation=1.26:brightness=0.01,"
            f"drawbox=y=0:h=330:color=black@0.40:t=fill,"
            f"drawbox=y=1280:h=640:color=black@0.40:t=fill,"
            f"drawtext={font_opt}text='SCIBYTES':fontcolor=#888888:fontsize=52:x=(w-text_w)/2:y=1750:shadowcolor=black@0.9:shadowx=2:shadowy=2,"
            f"drawtext={font_opt}text='{top_header}':fontcolor=#FFEA00:fontsize=36:x=(w-text_w)/2:y=170:borderw=4:bordercolor=black:shadowcolor=black@0.9:shadowx=2:shadowy=2,"
            f"drawtext={font_opt}text='{sub_header}':fontcolor=#FFFFFF:fontsize=48:x=(w-text_w)/2:y=240:borderw=5:bordercolor=black:shadowcolor=black@0.9:shadowx=3:shadowy=3"
            f"{sub_filter}[outv]"
        )

    # Audio Processing & Mixing
    # 1. 100% Stripping of source footage audio (never map 0:a to avoid clashing music/noise)
    # 2. Studio Mastering on Voiceover: low-end warmth + broadcast dynamic range compression
    voice_mastering = (
        "volume=1.0,equalizer=f=80:width_type=h:width=50:g=3.5,"
        "equalizer=f=3200:width_type=h:width=1200:g=1.5,"
        "compand=attacks=0.02:decays=0.1:points=-80/-80|-20/-10|0/-2"
    )

    bgm_path = os.path.join(os.path.dirname(__file__), 'assets', 'cosmic_ambient_drone.mp3')
    has_bgm = os.path.exists(bgm_path)
    extra_inputs = []

    if has_bgm:
        extra_inputs = ['-stream_loop', '-1', '-i', bgm_path]
        filter_complex += (
            f";[1:a]{voice_mastering}[voice_mastered];"
            f"[2:a]volume=0.10[bgm];"
            f"[voice_mastered][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]"
        )
    else:
        filter_complex += f";[1:a]{voice_mastering}[outa]"

    audio_maps = ['-map', '[outa]']

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
        *extra_inputs,
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

def build_cinematic_thumbnail_prompt(sub_header):
    lower = sub_header.lower()
    if any(k in lower for k in ['black hole', 'singularity', 'event horizon', 'gargantua']):
        return (
            f"insanely detailed photorealistic IMAX space photograph, supermassive black hole consuming space, "
            f"glowing orange and violet swirling accretion disk, gravitational lensing curving cosmic starlight, "
            f"ultra sharp 8k texture, cinematic dramatic lighting, volumetric glow, National Geographic astrophysics"
        )
    elif any(k in lower for k in ['sun', 'solar', 'flare', 'plasma', 'coronal']):
        return (
            f"extreme close-up 8k photography, massive solar flare erupting violently from the fiery surface of the Sun, "
            f"twisted loops of incandescent plasma in deep space, blinding white-hot corona, "
            f"NASA Solar Dynamics Observatory authentic photo, cinematic lighting, hyper-detailed"
        )
    elif any(k in lower for k in ['galaxy', 'milky way', 'andromeda', 'stars']):
        return (
            f"jaw-dropping 8K James Webb Space Telescope ultra-deep field photograph, majestic swirling spiral galaxy with "
            f"billions of glistening stars, glowing magenta and cyan cosmic dust clouds, extreme sharpness, "
            f"cinematic astrophysics documentary"
        )
    elif any(k in lower for k in ['planet', 'jupiter', 'saturn', 'mars']):
        return (
            f"photorealistic 8k close-up shot from deep space orbit of {sub_header}, "
            f"swirling turbulent atmospheric storm clouds, glowing rings in dark cosmos, "
            f"hyper-realistic space exploration photography, cinematic lighting"
        )
    elif any(k in lower for k in ['nebula', 'pillars of creation']):
        return (
            f"breathtaking 8k NASA James Webb Telescope photograph of cosmic nebula, "
            f"towering colorful pillars of gas and starbirth dust, glowing emerald, gold and violet hues, "
            f"hyper-detailed, authentic astrophysics"
        )
    else:
        return (
            f"awe-inspiring 8k IMAX space documentary photograph of {sub_header} in deep universe, "
            f"vibrant celestial colors, glowing cosmic dust, extreme focus, "
            f"National Geographic space edition, dramatic cinematic lighting"
        )

def generate_photorealistic_thumbnail(topic, output_thumbnail_path):
    print("Generating 100% free photorealistic AI thumbnail...")
    sub_header = topic.get('sub_header', topic['title'].split('#')[0].strip())
    top_header = topic.get('top_header', 'SCIBYTES DAILY')
    subs = topic.get('subtitles') or []
    first_sub = subs[0].get('text', sub_header) if subs else sub_header

    base_prompt = topic.get('thumb_prompt')
    if not base_prompt:
        base_prompt = build_cinematic_thumbnail_prompt(sub_header)

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

def normalize_script_cta(script_text):
    cleaned = re.sub(
        r'\s*Subscribe to\s+SciBytes\s+for\s+[^.!?]+[.!?]*\s*$',
        ' Subscribe to SciBytes for more interesting videos!',
        script_text,
        flags=re.IGNORECASE
    )
    if 'Subscribe to SciBytes' not in cleaned:
        cleaned = cleaned.rstrip() + ' Subscribe to SciBytes for more interesting videos!'
    return cleaned.strip()

def build_short_pipeline(topic):
    footage_path = os.path.join('temp', f"{topic['id']}_raw.mp4")
    if not os.path.exists(footage_path) or os.path.getsize(footage_path) == 0:
        download_footage(topic['footage_url'], footage_path)

    audio_path = os.path.join('temp', f"{topic['id']}_voice.mp3")
    ass_path = os.path.join('temp', f"{topic['id']}_subs.ass")
    spoken_script = normalize_script_cta(topic.get('script', ''))
    print(f"Generating voiceover and subtitles for '{topic['title']}'...")
    generate_voice(spoken_script, audio_path, ass_path)

    output_video = os.path.join(OUTPUT_DIR, 'scibytes_short_latest.mp4')
    print("Rendering vertical Short video with FFmpeg...")
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
    return True

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs('temp', exist_ok=True)

    exclude_ids = set()
    max_candidates = 5
    attempt = 0

    while attempt < max_candidates:
        attempt += 1
        try:
            topic = get_next_topic(exclude_ids=exclude_ids)
        except RuntimeError as e:
            print(f"CRITICAL: No more usable topics found in database: {e}")
            sys.exit(1)

        print("=" * 60)
        print(f"Attempt #{attempt}: Selected topic '{topic['title']}' (ID: {topic['id']})")
        print("=" * 60)

        try:
            build_short_pipeline(topic)
            print(f"SUCCESS: Topic '{topic['id']}' built completely and ready for upload!")
            return
        except Exception as e:
            print(f"WARNING: Issue encountered while building '{topic['id']}': {e}")
            print(f"Setting '{topic['id']}' aside and immediately switching to next queued topic for this upload slot...")
            exclude_ids.add(topic['id'])
            # Clean temporary files for this failed candidate
            raw_p = os.path.join('temp', f"{topic['id']}_raw.mp4")
            voice_p = os.path.join('temp', f"{topic['id']}_voice.mp3")
            subs_p = os.path.join('temp', f"{topic['id']}_subs.ass")
            for p in [raw_p, voice_p, subs_p]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            continue

    print(f"ERROR: Failed to build a short after trying {max_candidates} consecutive candidate topics.")
    sys.exit(1)

if __name__ == '__main__':
    main()
