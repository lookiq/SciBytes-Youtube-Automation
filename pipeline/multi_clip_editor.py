import os
import sys
import subprocess
import shutil
import random
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
for p in (PROJECT_ROOT, SCRIPT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from pipeline.build_short import (
    get_media_duration,
    get_bright_start_offset
)
from pipeline.branding_engine import (
    create_top_hook_card,
    create_floating_subscribe_pill
)

def build_segment_plan(total_duration, clip_sources, min_len=1.8, max_len=3.4):
    """
    Slices the total duration into dynamic micro-scenes (each 3.5s max, 1.8s - 3.4s).
    Cycles through 3 to 4 distinct cinematic clips and applies dynamic motion.
    """
    segments = []
    curr_time = 0.0
    num_sources = len(clip_sources)

    # Alternating motion styles
    effects = ['push', 'pull', 'punch', 'pan']
    source_idx = 0
    effect_idx = 0

    while curr_time < total_duration:
        remaining = total_duration - curr_time
        if remaining <= max_len:
            seg_len = remaining
        else:
            seg_len = round(random.uniform(min_len, max_len), 2)
            if (remaining - seg_len) < min_len:
                seg_len = remaining / 2.0

        src_info = clip_sources[source_idx % num_sources]
        src_path = src_info if isinstance(src_info, str) else src_info['path']
        
        # Check if source is external/viral to apply Anti-Content ID Shield
        is_external = any(k in os.path.basename(src_path).lower() for k in ['viral', 'youtube', 'tiktok', 'insta', 'download'])

        src_dur = get_media_duration(src_path)
        base_offset = 2.0 + (len(segments) * 6.5) % max(1.0, (src_dur - 8.0))
        start_offset = get_bright_start_offset(src_path, base_offset)

        effect = effects[effect_idx % len(effects)]
        transition = 'flash' if len(segments) > 0 and (len(segments) % 2 == 1) else 'cut'

        segments.append({
            'index': len(segments),
            'source_path': src_path,
            'is_external': is_external,
            'start_offset': start_offset,
            'duration': seg_len,
            'effect': effect,
            'transition': transition,
            'timeline_start': curr_time,
            'timeline_end': curr_time + seg_len
        })

        curr_time += seg_len
        source_idx += 1
        effect_idx += 1

    return segments

def render_micro_segment(seg, temp_dir):
    """
    Renders an individual micro-clip with:
    - Vertical 9:16 framing (1080x1920)
    - Anti-Content ID Shield (Horizontal Flip, 1.04x speed shift, audio stripping)
    - Dynamic motion zoom/pan
    - Color grading & flash transition
    """
    out_path = os.path.join(temp_dir, f"mc_seg_{seg['index']:03d}.mp4")
    dur = seg['duration']
    effect = seg['effect']
    is_external = seg['is_external']

    # 1. Anti-Content ID Filters
    # Horizontal Flip + 1.04x Speed Shift on external clips
    shield_filters = []
    if is_external:
        shield_filters.append("hflip")
        shield_filters.append("setpts=PTS/1.04")

    # 2. Dynamic Motion Filters (eval=frame with even integer truncation)
    if effect == 'push':
        motion = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"scale=w='trunc(1080*(1+0.12*t/{dur})/2)*2':h='trunc(1920*(1+0.12*t/{dur})/2)*2':eval=frame,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2"
        )
    elif effect == 'pull':
        motion = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"scale=w='trunc(1080*(1.12-0.10*t/{dur})/2)*2':h='trunc(1920*(1.12-0.10*t/{dur})/2)*2':eval=frame,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2"
        )
    elif effect == 'punch':
        motion = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"scale=w='trunc(1080*(1.14+0.03*t/{dur})/2)*2':h='trunc(1920*(1.14+0.03*t/{dur})/2)*2':eval=frame,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2"
        )
    else:  # pan
        motion = (
            f"scale=1180:2098:force_original_aspect_ratio=increase,crop=1180:2098,"
            f"crop=1080:1920:'trunc((in_w-1080)*0.5 + (in_w-1080)*0.35*(t/{dur}-0.5)/2)*2':'(in_h-1920)/2'"
        )

    # 3. Transition Filter
    trans_filter = ""
    if seg['transition'] == 'flash':
        trans_filter = ",fade=t=in:st=0:d=0.07:color=white"

    # Assemble full filter chain
    prefix = ",".join(shield_filters) + ("," if shield_filters else "")
    vf = f"{prefix}{motion},eq=contrast=1.16:saturation=1.28:brightness=0.01{trans_filter},fps=30,format=yuv420p"

    # Extract slightly longer source slice if 1.04x speed shift is applied
    source_slice = dur * 1.04 if is_external else dur

    cmd = [
        'ffmpeg', '-y',
        '-ss', str(seg['start_offset']),
        '-i', seg['source_path'],
        '-t', str(source_slice),
        '-vf', vf,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '18',
        '-an',  # Complete Audio Stripping for 100% Anti-Content ID Protection
        out_path
    ]

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_path

def assemble_multi_clip_video(clip_sources, total_duration, output_video_path, temp_dir='temp'):
    """
    Assembles a montage of 3-4 clips (each max 3.5s) with Anti-Content ID Shield,
    motion zooms, and flash cuts.
    Returns list of cut timestamps for audio sound effects.
    """
    os.makedirs(temp_dir, exist_ok=True)
    plan = build_segment_plan(total_duration, clip_sources)
    print(f"Divided timeline into {len(plan)} dynamic montage clips (each <= 3.5s):")
    for s in plan:
        base_name = os.path.basename(s['source_path'])
        shield = " [Anti-Content ID Shield]" if s['is_external'] else ""
        print(f"  Clip {s['index']+1}: {s['timeline_start']:.1f}s -> {s['timeline_end']:.1f}s ({s['duration']:.1f}s) | Source: {base_name[:24]} | FX: {s['effect']}{shield}")

    seg_paths = []
    cut_timestamps = []
    for s in plan:
        p = render_micro_segment(s, temp_dir)
        seg_paths.append(p)
        if s['timeline_start'] > 0.1:
            cut_timestamps.append(s['timeline_start'])

    # Write concat manifest
    manifest_path = os.path.join(temp_dir, 'multi_clip_manifest.txt')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        for p in seg_paths:
            clean_path = os.path.abspath(p).replace('\\', '/')
            f.write(f"file '{clean_path}'\n")

    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', manifest_path,
        '-c', 'copy',
        output_video_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Seamlessly stitched {len(seg_paths)} micro-clips: {output_video_path}")
    return cut_timestamps

def render_multi_clip_short(topic, clip_sources, audio_path, output_path, ass_path=None):
    """
    Full pipeline rendering multi-clip Short with:
    1. Montage Pacing (3 to 4 clips, each 3.5s max)
    2. Anti-Content ID Shield (hflip, 1.04x speed, audio stripping)
    3. Branded Visual Top Hook Card (Box 2) with Color Psychology tags
    4. Floating Subscribe Pill Badge (Box 3) in final 3.5 seconds
    5. Synchronized Whoosh SFX on cuts + Bass drop opening + Cosmic BGM
    6. Dynamic active-word CapCut yellow pop ASS subtitles (Box 1)
    7. Direct Desktop preview synchronization
    """
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    duration = get_media_duration(audio_path)
    print(f"Rendering Multi-Clip Short (Duration: {duration:.2f}s)...")

    # Step 1: Assemble video montage of micro-clips (max 3.5s each)
    montage_raw = os.path.join(temp_dir, f"{topic['id']}_montage_raw.mp4")
    cut_timestamps = assemble_multi_clip_video(clip_sources, duration, montage_raw, temp_dir)

    # Step 2: Generate Branded Overlays (Top Hook Card & Floating Subscribe Pill)
    top_card_path = os.path.join(temp_dir, f"{topic['id']}_top_card.png")
    create_top_hook_card(topic['title'], dest_path=top_card_path)

    sub_pill_path = os.path.join(temp_dir, "floating_subscribe_pill.png")
    create_floating_subscribe_pill(dest_path=sub_pill_path)

    # Step 3: Sound Design & Audio Mixing
    voice_mastering = (
        "volume=1.0,equalizer=f=80:width_type=h:width=50:g=3.5,"
        "equalizer=f=3200:width_type=h:width=1200:g=1.5,"
        "compand=attacks=0.02:decays=0.1:points=-80/-80|-20/-10|0/-2"
    )

    bgm_path = os.path.join(SCRIPT_DIR, 'assets', 'cosmic_ambient_drone.mp3')
    bass_path = os.path.join(SCRIPT_DIR, 'assets', 'bass_impact.mp3')
    whoosh_path = os.path.join(SCRIPT_DIR, 'assets', 'whoosh_sfx.mp3')

    # Sequential input files list
    # Input 0: montage_raw (video)
    # Input 1: audio_path (voice)
    # Input 2: top_card_path (overlay image)
    # Input 3: sub_pill_path (overlay image)
    inputs = [
        '-i', montage_raw,
        '-i', audio_path,
        '-i', top_card_path,
        '-i', sub_pill_path
    ]
    input_file_index = 4

    audio_chains = []
    audio_chains.append(f"[1:a]{voice_mastering}[voice_clean]")
    mix_sources = ["[voice_clean]"]

    # Background music
    if os.path.exists(bgm_path):
        bgm_idx = input_file_index
        inputs.extend(['-stream_loop', '-1', '-i', bgm_path])
        input_file_index += 1
        audio_chains.append(f"[{bgm_idx}:a]volume=0.08[bgm_clean]")
        mix_sources.append("[bgm_clean]")

    # Bass impact at t=0.0s
    if os.path.exists(bass_path):
        bass_idx = input_file_index
        inputs.extend(['-i', bass_path])
        input_file_index += 1
        audio_chains.append(f"[{bass_idx}:a]volume=0.25[bass_clean]")
        mix_sources.append("[bass_clean]")

    # Whoosh SFX at each cut timestamp
    if os.path.exists(whoosh_path) and cut_timestamps:
        whoosh_idx = input_file_index
        inputs.extend(['-i', whoosh_path])
        input_file_index += 1
        delayed_whooshes = []
        for w_i, cut_t in enumerate(cut_timestamps[:10]):
            delay_ms = int(max(0, cut_t - 0.05) * 1000)
            delayed_whooshes.append(f"[{whoosh_idx}:a]adelay={delay_ms}|{delay_ms},volume=0.20[w_{w_i}]")
            mix_sources.append(f"[w_{w_i}]")
        audio_chains.extend(delayed_whooshes)

    amix_filter = f"{';'.join(audio_chains)};{''.join(mix_sources)}amix=inputs={len(mix_sources)}:duration=first:dropout_transition=2[outa]"

    # Step 4: Video Compositing
    # Layer 0: Base montage video + Vignette + Bottom Safe Shadow
    # Layer 1: Top Hook Card (Box 2)
    # Layer 2: Dynamic ASS Subtitles (Box 1)
    # Layer 3: Floating Subscribe Pill Badge (Box 3, final 3.5 seconds)
    sub_filter = ""
    if ass_path and os.path.exists(ass_path):
        rel_ass = os.path.relpath(ass_path).replace('\\', '/')
        sub_filter = f",ass={rel_ass}"

    outro_start = max(0.0, duration - 3.5)

    video_filter = (
        f"[0:v]vignette=angle=0.34,drawbox=y=1340:h=580:color=black@0.42:t=fill[v_base];"
        f"[v_base][2:v]overlay=0:0[v_card];"
        f"[v_card]null{sub_filter}[v_subs];"
        f"[v_subs][3:v]overlay=0:0:enable='between(t,{outro_start:.2f},{duration:.2f})'[outv]"
    )

    full_filter = f"{video_filter};{amix_filter}"

    safe_title = topic.get('title', 'SciBytes Short').replace('"', '').replace("'", "")
    container_metadata = [
        '-metadata', f'title={safe_title}',
        '-metadata', 'artist=SciBytes',
        '-metadata', 'album=SciBytes Multi-Clip Shorts',
        '-metadata', 'genre=Science & Technology'
    ]

    ffmpeg_cmd = [
        'ffmpeg', '-y',
        *inputs,
        '-filter_complex', full_filter,
        '-map', '[outv]',
        '-map', '[outa]',
        *container_metadata,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        output_path
    ]

    print("Rendering final master composite with Anti-Content ID Shield, Top Card, Subtitles, SFX, and Hybrid CTA Badge...")
    subprocess.run(ffmpeg_cmd, check=True)
    print(f"Multi-clip Short rendered successfully: {output_path}")

    # Synchronize to Desktop preview
    desktop_dir = os.path.join(os.environ.get('USERPROFILE', os.path.expanduser('~')), 'Desktop')
    desktop_video = os.path.join(desktop_dir, 'SciBytes_Viral_Short_Preview.mp4')
    try:
        shutil.copy2(output_path, desktop_video)
        print(f"Direct Desktop video preview updated: {desktop_video}")
    except Exception as e:
        print(f"Notice during Desktop copy: {e}")
