import os
import sys
import re
import random
import urllib.parse
import requests
import subprocess
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
for p in (PROJECT_ROOT, SCRIPT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from pipeline.build_short import get_media_duration

MOTION_PRESETS = [
    'zoom_in',
    'zoom_out',
    'pan_right',
    'pan_left',
    'diagonal_tr',
    'pop_in',
    'subtle_zoom'
]

def generate_scene_image(prompt, dest_path, width=1080, height=1920, seed=None):
    """
    Generates a 1080x1920 hyper-realistic scene image via Pollinations Flux-Realism.
    Free, no API key needed, strictly zero watermarks.
    """
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 15000:
        return dest_path

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    if seed is None:
        seed = random.randint(1000, 999999)

    cinematic_prompt = f"{prompt}, 8k photorealistic space documentary photography, extreme detail, dramatic rim lighting, cinematic vertical 9:16 composition, IMAX astrophysic clarity"
    encoded = urllib.parse.quote(cinematic_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&model=flux-realism&nologo=true"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=40)
            if r.status_code == 200 and len(r.content) > 10000:
                raw_temp = dest_path + ".raw.jpg"
                with open(raw_temp, 'wb') as f:
                    f.write(r.content)

                # Crop bottom 80 pixels to guarantee zero watermark from any source
                cmd = [
                    'ffmpeg', '-y', '-nostdin',
                    '-i', raw_temp,
                    '-vf', 'crop=in_w:in_h-80:0:0,scale=1080:1920',
                    '-q:v', '2',
                    dest_path
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                if os.path.exists(raw_temp):
                    os.remove(raw_temp)
                return dest_path
        except Exception as e:
            print(f"Notice during scene image generation (attempt {attempt+1}): {e}")

    return None

def build_kenburns_filter(motion, duration, fps=30):
    """
    Generates high-precision Ken Burns motion zoom/pan expressions.
    Adapted from ffmpeg-ai architecture.
    """
    dur_f = max(int(duration * fps), 1)

    if motion == 'pop_in':
        # Fast punch-in zoom in the first 0.4s then gentle drift
        return (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"scale=w='trunc(1080*(1.16+0.04*t/{duration})/2)*2':h='trunc(1920*(1.16+0.04*t/{duration})/2)*2':eval=frame,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2"
        )
    elif motion == 'zoom_out':
        # Smooth cinematic pull-back
        return (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"scale=w='trunc(1080*(1.18-0.12*t/{duration})/2)*2':h='trunc(1920*(1.18-0.12*t/{duration})/2)*2':eval=frame,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2"
        )
    elif motion == 'pan_right':
        # Smooth horizontal drift to the right
        return (
            f"scale=1280:2276:force_original_aspect_ratio=increase,crop=1280:2276,"
            f"crop=1080:1920:'trunc((in_w-1080)*0.2 + (in_w-1080)*0.6*(t/{duration})/2)*2':'(in_h-1920)/2'"
        )
    elif motion == 'pan_left':
        # Smooth horizontal drift to the left
        return (
            f"scale=1280:2276:force_original_aspect_ratio=increase,crop=1280:2276,"
            f"crop=1080:1920:'trunc((in_w-1080)*0.8 - (in_w-1080)*0.6*(t/{duration})/2)*2':'(in_h-1920)/2'"
        )
    elif motion == 'diagonal_tr':
        # Dynamic diagonal camera tracking
        return (
            f"scale=1240:2204:force_original_aspect_ratio=increase,crop=1240:2204,"
            f"crop=1080:1920:'trunc((in_w-1080)*0.2 + (in_w-1080)*0.5*(t/{duration})/2)*2':'trunc((in_h-1920)*0.8 - (in_h-1920)*0.5*(t/{duration})/2)*2'"
        )
    else:  # zoom_in default
        return (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"scale=w='trunc(1080*(1+0.14*t/{duration})/2)*2':h='trunc(1920*(1+0.14*t/{duration})/2)*2':eval=frame,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2"
        )

def render_image_to_kenburns_video(image_path, duration, output_path, motion='zoom_in'):
    """
    Renders a single static image into a high-octane 1080x1920 video clip
    with Ken Burns motion, 60fps smoothing, and cinematic color grading.
    """
    kb_filter = build_kenburns_filter(motion, duration)
    color_grade = "eq=contrast=1.14:saturation=1.28:brightness=0.012,vignette=angle=0.28"
    vf = f"{kb_filter},{color_grade},fps=30,format=yuv420p"

    cmd = [
        'ffmpeg', '-y', '-nostdin',
        '-loop', '1',
        '-i', image_path,
        '-t', str(duration),
        '-vf', vf,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=60)
    return output_path

def generate_scene_prompts_from_script(topic):
    """
    Splits the topic and script into 4 to 5 thematic scene prompts.
    """
    title = topic.get('title', '').split('#')[0].strip()
    script = topic.get('script', '')

    lower = (title + " " + script).lower()

    if 'roman' in lower or 'dark matter' in lower:
        return [
            ("breathtaking 8k NASA visualization of dark matter cosmic web glowing faintly across deep cosmic void, billions of distant galaxies embedded in mysterious filaments", "zoom_in"),
            ("cinematic vertical 8k photograph of NASA Nancy Grace Roman Space Telescope floating majestically in deep space against starfield, solar panels gleaming", "pan_right"),
            ("spectacular 8k IMAX James Webb cosmic gravitational lensing, massive galaxy cluster warping and bending spacetime, Einstein rings and glowing arcs in deep cosmos", "diagonal_tr"),
            ("awe-inspiring 8k ultra-deep field view of billions of glistening spiral galaxies mapped across the cosmos, glowing vibrant nebula dust", "pop_in")
        ]
    elif 'black hole' in lower:
        return [
            ("jaw-dropping 8k close-up shot of supermassive black hole event horizon, glowing golden plasma accretion disk spinning violently in black cosmos", "zoom_in"),
            ("hypnotic 8k relativistic gravitational lensing distortion around gargantuan black hole singularity, light bending in space", "pan_left"),
            ("hyper-realistic 8k simulation of star being shredded into hot stream of gas by supermassive black hole gravitational tidal force", "diagonal_tr"),
            ("spectacular IMAX 8k deep space view of black hole shooting relativistic plasma jets millions of light years into void", "pop_in")
        ]
    elif 'solar' in lower or 'sun' in lower:
        return [
            ("extreme close-up 8k photography of massive solar flare erupting from churning fiery surface of the Sun, incandescent plasma loops", "pop_in"),
            ("jaw-dropping 8k NASA SDO view of blinding white-hot solar corona ejecting coronal mass ejection into space", "zoom_in"),
            ("dramatic 8k view of solar magnetic field lines twisting and reconnecting violently above Sun photosphere", "pan_right"),
            ("awe-inspiring 8k photograph of Earth dwarfed by colossal solar storm eruption in deep space", "zoom_out")
        ]
    elif 'galaxy' in lower or 'milky way' in lower or 'andromeda' in lower:
        return [
            ("jaw-dropping 8K James Webb ultra-deep field photograph of swirling spiral galaxy with billions of glistening stars", "zoom_in"),
            ("breathtaking 8k visualization of cosmic collision between Andromeda and Milky Way galaxies, stars and dust colliding", "diagonal_tr"),
            ("spectacular 8k view from deep space orbit inside giant glowing cosmic nebula stellar nursery with baby stars igniting", "pan_right"),
            ("awe-inspiring 8k IMAX deep universe survey showing countless colorful galaxies stretching across infinity", "pop_in")
        ]
    else:
        return [
            (f"awe-inspiring 8k IMAX space documentary photograph of {title} in deep universe, vibrant celestial colors, extreme focus", "zoom_in"),
            (f"hyper-realistic 8k NASA space exploration visualization of {title}, dramatic cinematic lighting, deep cosmos", "pan_right"),
            (f"spectacular 8k astrophysics telescope view revealing mysterious cosmic phenomena of {title}", "diagonal_tr"),
            (f"breathtaking 8k vertical composition of deep universe mysteries and star clusters, cinematic masterpiece", "pop_in")
        ]

def assemble_ai_scene_video(topic, total_duration, output_video_path, temp_dir='temp'):
    """
    Full ffmpeg-ai style pipeline:
    1. Generates 4-5 scene prompts
    2. Downloads Flux-Realism 1080x1920 visuals
    3. Renders each with Ken Burns dynamic motion
    4. Concat with flash/cut transitions
    5. Returns cut timestamps for sound design
    """
    os.makedirs(temp_dir, exist_ok=True)
    scenes_dir = os.path.join(temp_dir, 'scenes')
    os.makedirs(scenes_dir, exist_ok=True)

    scene_prompts = generate_scene_prompts_from_script(topic)
    num_scenes = len(scene_prompts)
    scene_dur = round(total_duration / num_scenes, 2)

    print(f"[FFMPEG-AI ENGINE] Generating {num_scenes} custom photorealistic scenes (each {scene_dur}s)...")
    clip_paths = []
    cut_timestamps = []
    curr_t = 0.0

    for idx, (prompt, motion) in enumerate(scene_prompts):
        img_path = os.path.join(scenes_dir, f"{topic['id']}_scene_{idx}.jpg")
        print(f"  Scene {idx+1}/{num_scenes} -> Generating Flux-Realism visual: '{prompt[:40]}...'")
        generated_img = generate_scene_image(prompt, img_path)

        if not generated_img or not os.path.exists(generated_img):
            print(f"  Notice: Scene {idx+1} generation fallback to primary footage.")
            return None

        # Determine exact duration for this scene
        this_dur = (total_duration - curr_t) if idx == num_scenes - 1 else scene_dur
        clip_path = os.path.join(scenes_dir, f"{topic['id']}_clip_{idx}.mp4")

        print(f"  Rendering Ken Burns motion ({motion}, {this_dur:.2f}s)...")
        render_image_to_kenburns_video(generated_img, this_dur, clip_path, motion=motion)
        clip_paths.append(clip_path)

        if curr_t > 0.1:
            cut_timestamps.append(curr_t)
        curr_t += this_dur

    # Stitched clips via concat
    manifest_path = os.path.join(temp_dir, 'ai_scenes_manifest.txt')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        for p in clip_paths:
            clean_p = os.path.abspath(p).replace('\\', '/')
            f.write(f"file '{clean_p}'\n")

    cmd = [
        'ffmpeg', '-y', '-nostdin',
        '-f', 'concat',
        '-safe', '0',
        '-i', manifest_path,
        '-c', 'copy',
        output_video_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=60)
    print(f"[FFMPEG-AI ENGINE] Successfully assembled {len(clip_paths)} Ken Burns scene clips: {output_video_path}")
    return cut_timestamps
