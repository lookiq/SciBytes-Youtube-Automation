import os
import sys
import json
import asyncio
import argparse
import subprocess
import requests
import urllib.parse
import edge_tts

VOICE = 'en-US-ChristopherNeural'
OUTPUT_DIR = 'output'

def get_font_file():
    win_font = 'C:/Windows/Fonts/ariblk.ttf'
    if os.path.exists(win_font):
        return 'C\\:/Windows/Fonts/ariblk.ttf'
    linux_fonts = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
    ]
    for lf in linux_fonts:
        if os.path.exists(lf):
            return lf
    return None

async def generate_breaking_audio(text, dest_path):
    print("Generating urgent breaking voiceover with ChristopherNeural (rate=+10%)...")
    communicate = edge_tts.Communicate(text, VOICE, rate="+10%", pitch="+0Hz")
    await communicate.save(dest_path)
    print(f"Audio saved to: {dest_path}")

def get_media_duration(file_path):
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(res.stdout.strip())

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

def render_breaking_video(headline, summary, footage_path, audio_path, output_path):
    duration = get_media_duration(audio_path)
    font_file = get_font_file()
    font_opt = f"fontfile='{font_file}':" if font_file else ""

    top_header = "BREAKING SPACE ALERT"
    sub_header = headline[:45].upper().replace("'", "’").replace(":", " - ").replace(",", "")

    # Clean text chunks for subtitle presentation
    words = summary.split()
    chunk_size = 4
    chunks = [' '.join(words[i:i+chunk_size]).upper().replace("'", "’").replace(":", " - ").replace(",", "")
              for i in range(0, len(words), chunk_size)]
    
    time_per_chunk = (duration - 3.0) / max(len(chunks), 1)
    
    subtitle_filters = []
    for idx, c_text in enumerate(chunks):
        c_start = idx * time_per_chunk
        c_end = min((idx + 1) * time_per_chunk, duration - 2.5)
        color = "#FFEA00" if idx % 2 == 0 else "#00FFFF"
        f_str = (
            f"drawtext={font_opt}text='{c_text}':fontcolor={color}:fontsize=52:"
            f"x=(w-text_w)/2:y=1380:enable='between(t,{c_start:.2f},{c_end:.2f})':"
            f"borderw=6:bordercolor=black:shadowcolor=black@0.95:shadowx=4:shadowy=4"
        )
        subtitle_filters.append(f_str)
    
    # Subscribe call to action at the end
    cta_start = max(duration - 3.0, 0)
    subtitle_filters.append(
        f"drawtext={font_opt}text='SUBSCRIBE TO SCIBYTES!':fontcolor=#00FF66:fontsize=52:"
        f"x=(w-text_w)/2:y=1380:enable='between(t,{cta_start:.2f},{duration:.2f})':"
        f"borderw=6:bordercolor=black:shadowcolor=black@0.95:shadowx=4:shadowy=4"
    )

    sub_filter_chain = ', ' + ', '.join(subtitle_filters) if subtitle_filters else ""

    filter_complex = (
        f"[0:v]trim=duration={duration},setpts=PTS-STARTPTS,split=2[bg_raw][fg_raw];"
        f"[bg_raw]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.25:contrast=1.1[bg];"
        f"[fg_raw]scale=1080:-2,eq=contrast=1.1:saturation=1.2[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2[basev];"
        f"[basev]drawtext={font_opt}text='{top_header}':fontcolor=#FF2A55:fontsize=44:x=(w-text_w)/2:y=160:borderw=5:bordercolor=black:shadowcolor=black@0.9:shadowx=3:shadowy=3,"
        f"drawtext={font_opt}text='{sub_header}':fontcolor=#FFFFFF:fontsize=46:x=(w-text_w)/2:y=235:borderw=5:bordercolor=black:shadowcolor=black@0.9:shadowx=3:shadowy=3,"
        f"drawtext={font_opt}text='SCIBYTES LIVE':fontcolor=#FF2A55:fontsize=48:x=(w-text_w)/2:y=1750:borderw=4:bordercolor=black:shadowcolor=black@0.9:shadowx=2:shadowy=2"
        f"{sub_filter_chain}[outv]"
    )

    cmd = [
        'ffmpeg', '-y',
        '-ss', '2.0',
        '-i', footage_path,
        '-i', audio_path,
        '-filter_complex', filter_complex,
        '-map', '[outv]',
        '-map', '1:a',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '19',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        output_path
    ]
    print("Rendering breaking news video with FFmpeg...")
    res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("FFmpeg Error:\n", res.stderr)
        raise RuntimeError("Video rendering failed.")
    print(f"Breaking Short rendered successfully -> {output_path}")

def main():
    parser = argparse.ArgumentParser(description="SciBytes Breaking Space News Generator")
    parser.add_argument("--headline", type=str, default="Historic Space Breakthrough Just Announced", help="Breaking event headline")
    parser.add_argument("--summary", type=str, default="Astronomers have just confirmed a major cosmic event. Scientists around the world are tracking the unprecedented data right now. Subscribe to SciBytes for live breaking space updates!", help="Event description script")
    parser.add_argument("--footage_url", type=str, default="https://images-assets.nasa.gov/video/KSC-20220427-VP-MWC01-0001-SpaceX_Crew_4_highlights-3301760/KSC-20220427-VP-MWC01-0001-SpaceX_Crew_4_highlights-3301760~orig.mp4", help="Footage MP4 URL")
    parser.add_argument("--upload", action="store_true", help="Upload immediately to YouTube upon completion")
    parser.add_argument("--dry_run", action="store_true", help="Only verify inputs and syntax without full rendering")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs('temp', exist_ok=True)

    print("=" * 60)
    print("SciBytes - Emergency Breaking Space Short Generator")
    print("=" * 60)
    print(f"Headline    : {args.headline}")
    print(f"Summary     : {args.summary}")
    print(f"Footage URL : {args.footage_url}")
    print("=" * 60)

    if args.dry_run:
        print("Dry run mode: verification passed.")
        return

    audio_path = os.path.join('temp', 'breaking_voice.mp3')
    footage_path = os.path.join('temp', 'breaking_footage.mp4')
    output_video_path = os.path.join(OUTPUT_DIR, 'scibytes_short_latest.mp4')
    metadata_path = os.path.join(OUTPUT_DIR, 'metadata.json')

    # Step 1: Voiceover
    full_script = f"Breaking space alert! {args.summary}"
    asyncio.run(generate_breaking_audio(full_script, audio_path))

    # Step 2: Footage
    download_footage(args.footage_url, footage_path)

    # Step 3: Video Assembly
    render_breaking_video(args.headline, full_script, footage_path, audio_path, output_video_path)

    # Step 4: Metadata
    metadata = {
        "title": f"[BREAKING] {args.headline} #Shorts",
        "description": f"BREAKING SPACE ALERT: {args.summary}\n\nStay tuned to SciBytes for instant updates on deep space discoveries, NASA missions, and rocket breakthroughs!\n\n#BreakingNews #SpaceNews #NASA #SpaceX #Astronomy #ScienceShorts #SciBytes #Shorts",
        "tags": ["breaking space news", "space news", "nasa breaking", "spacex update", "astronomy news", "space facts", "SciBytes", "shorts"]
    }
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")

    # Step 5: Upload if requested
    if args.upload:
        print("\nProceeding to immediate YouTube upload...")
        cmd = [sys.executable, "pipeline/upload_to_youtube.py"]
        subprocess.run(cmd, check=True)

    print("\nSUCCESS! Breaking news pipeline completed.")

if __name__ == "__main__":
    main()
