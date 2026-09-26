import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
for p in (PROJECT_ROOT, SCRIPT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import argparse
import json
import urllib.parse
import shutil
import subprocess

try:
    from pipeline.transcript_engine import extract_transcript_from_url
    from pipeline.script_reengineer import reengineer_script
    from pipeline.build_short import generate_voice, download_footage, generate_photorealistic_thumbnail
    from pipeline.seo_engine import generate_seo_metadata
    from pipeline.cinematic_footage_engine import get_cinematic_montage_pool, get_cinematic_space_footage
    from pipeline.multi_clip_editor import render_multi_clip_short
except ImportError:
    from transcript_engine import extract_transcript_from_url
    from script_reengineer import reengineer_script
    from build_short import generate_voice, download_footage, generate_photorealistic_thumbnail
    from seo_engine import generate_seo_metadata
    from cinematic_footage_engine import get_cinematic_montage_pool, get_cinematic_space_footage
    from multi_clip_editor import render_multi_clip_short

def process_viral_short(youtube_url, upload=False):
    print("=" * 65)
    print("SCIBYTES 4-PILLAR VIRAL MULTI-CLIP MONTAGE GENERATOR")
    print(f"Target Video URL: {youtube_url}")
    print("=" * 65)

    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    output_video = os.path.join(PROJECT_ROOT, output_dir, 'scibytes_short_latest.mp4')
    if os.path.exists(output_video):
        try:
            os.remove(output_video)
        except Exception:
            pass

    # Step 1: Extract Transcript & Metadata
    ext = extract_transcript_from_url(youtube_url)
    raw_title = ext['title']
    raw_transcript = ext['transcript']

    # Step 2: AI Re-engineer Script with Hybrid CTA Outro
    print("\nStep 2: Re-engineering script with Provocative Science Question & Hybrid CTA Outro...")
    reengineered = reengineer_script(raw_title, raw_transcript)
    print(f"Title: {reengineered['title']}")
    print(f"Script: {reengineered['script']}")

    clean_id = "viral_" + "".join(c for c in reengineered['title'] if c.isalnum() or c in ('_', '-')).lower()[:25]
    topic = {
        "id": clean_id,
        "title": reengineered['title'],
        "top_header": reengineered.get('top_header', 'COSMIC DISCOVERY'),
        "sub_header": reengineered.get('sub_header', reengineered['title'].split('#')[0].strip()),
        "script": reengineered['script']
    }

    # Step 3: Fetch Multiple Footages (Viral Reference + Curated 4K Cosmic Vault)
    print("\nStep 3: Curating 3 to 4 High-Definition 4K Footage Sources for Montage Vault...")
    footage_sources = []

    # 3a. Download viral source video for Anti-Content ID shielded clips
    viral_footage_path = os.path.join(temp_dir, f"{clean_id}_viral_raw.mp4")
    if not os.path.exists(viral_footage_path) or os.path.getsize(viral_footage_path) == 0:
        print("Downloading viral reference footage...")
        try:
            cmd = ['yt-dlp', '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', '-o', viral_footage_path, youtube_url]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Notice during viral download: {e}")

    if os.path.exists(viral_footage_path) and os.path.getsize(viral_footage_path) > 100000:
        footage_sources.append(viral_footage_path)

    # 3b. Curate 4K NASA / ESA / Transformative CGI clips
    cosmic_urls = get_cinematic_montage_pool(reengineered['title'], count=3)
    for c_i, c_url in enumerate(cosmic_urls):
        local_c_path = os.path.join(temp_dir, f"cosmic_vault_{c_i}.mp4")
        if not os.path.exists(local_c_path) or os.path.getsize(local_c_path) == 0:
            download_footage(c_url, local_c_path)
        if os.path.exists(local_c_path) and os.path.getsize(local_c_path) > 50000:
            footage_sources.append(local_c_path)

    # Fallback to existing library if empty
    if not footage_sources:
        for f in ['black_hole_spaghettification_raw.mp4', 'jwst_deep_field_galaxies_raw.mp4']:
            fp = os.path.join(temp_dir, f)
            if os.path.exists(fp):
                footage_sources.append(fp)

    print(f"Total verified montage footage sources: {len(footage_sources)}")

    # Step 4: Voiceover & Dynamic ASS Subtitles
    print("\nStep 4: Generating voiceover with studio mastering and verbatim timestamps...")
    audio_path = os.path.join(temp_dir, f"{clean_id}_voice.mp3")
    ass_path = os.path.join(temp_dir, f"{clean_id}_subs.ass")
    generate_voice(topic['script'], audio_path, ass_path)

    # Step 5: Render Multi-Clip Short (Montage Pacing, Anti-Content ID, Top Card, Subscribe Pill, SFX)
    print("\nStep 5: Rendering 4-Pillar Multi-Clip Short with FFmpeg...")
    render_multi_clip_short(topic, footage_sources, audio_path, output_video, ass_path)

    # Step 6: 3D Realistic 4K Thumbnail Generation
    print("\nStep 6: Generating 3D Realistic 4K AI Thumbnail...")
    thumb_path = os.path.join(output_dir, 'thumbnail.jpg')
    generate_photorealistic_thumbnail(topic, thumb_path)

    # Step 7: 100% SEO Metadata Generation
    print("\nStep 7: Generating VidIQ & TubeBuddy compliant SEO Metadata...")
    seo = generate_seo_metadata(topic)
    meta_path = os.path.join(output_dir, 'metadata.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(seo, f, indent=2)

    # Step 8: Optional Direct Upload
    if upload:
        print("\nUploading finished Short to YouTube Studio...")
        from pipeline.upload_to_youtube import get_authenticated_service, upload_video
        youtube = get_authenticated_service()
        upload_video(youtube, topic)

    # Direct Desktop Preview Synchronization
    desktop_dir = os.path.join(os.environ.get('USERPROFILE', os.path.expanduser('~')), 'Desktop')
    desktop_video = os.path.join(desktop_dir, 'SciBytes_Viral_Short_Preview.mp4')
    desktop_thumb = os.path.join(desktop_dir, 'SciBytes_Thumbnail_Preview.jpg')
    try:
        if os.path.exists(output_video):
            shutil.copy2(output_video, desktop_video)
            print(f"Desktop Video Preview updated: {desktop_video}")
        if os.path.exists(thumb_path):
            shutil.copy2(thumb_path, desktop_thumb)
            print(f"Desktop Thumbnail Preview updated: {desktop_thumb}")
    except Exception as e:
        print(f"Notice during Desktop copy: {e}")

    print("\n" + "=" * 65)
    print("4-PILLAR VIRAL SHORT GENERATION COMPLETE!")
    print(f"Desktop Preview : {desktop_video}")
    print(f"Thumbnail       : {desktop_thumb}")
    print(f"SEO Metadata    : {meta_path}")
    print("=" * 65)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create SciBytes Short with 4-Pillar Architecture")
    parser.add_argument('--url', required=True, help="YouTube Short or Video URL to replicate")
    parser.add_argument('--upload', action='store_true', help="Upload directly to YouTube upon completion")
    args = parser.parse_args()

    process_viral_short(args.url, upload=args.upload)
