import asyncio
import subprocess
import edge_tts

SCRIPT = (
    "What happens if you jump into Jupiter? "
    "First of all, you can never land on it, because Jupiter has no solid surface at all. "
    "As you plunge into the swirling clouds, temperatures soar over ten thousand degrees, "
    "and the atmospheric pressure becomes so intense, it would crush a nuclear submarine like a soda can. "
    "Subscribe to Daily Dose of Physics for more cosmic mysteries!"
)

async def generate_voice():
    communicate = edge_tts.Communicate(SCRIPT, "en-US-ChristopherNeural", rate="+6%")
    await communicate.save("jupiter_voice.mp3")
    print("Jupiter voice generated.")

def render_short():
    ffprobe_cmd = 'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 jupiter_voice.mp3'
    duration = float(subprocess.check_output(ffprobe_cmd, shell=True, text=True).strip())
    print(f"Voice duration: {duration:.2f}s")

    # Broadcast Shorts Layout:
    # 1. Background: blurred ambient space from NASA clip
    # 2. Foreground: sharp 1080p center zoom on Jupiter
    # 3. Text: Top Channel Branding, Mid/Low Dynamic Headlines
    ffmpeg_cmd = (
        f'ffmpeg -y -ss 5 -i nasa_jupiter_raw.mp4 -i jupiter_voice.mp3 '
        f'-filter_complex "'
        f'[0:v]trim=duration={duration},setpts=PTS-STARTPTS,split=2[orig1][orig2]; '
        f'[orig1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:10[bg]; '
        f'[orig2]scale=1080:-1[fg]; '
        f'[bg][fg]overlay=0:(1920-overlay_h)/2[vid]; '
        f'[vid]drawtext=text=\'DAILY DOSE OF PHYSICS\':fontcolor=yellow:fontsize=46:x=(w-text_w)/2:y=180:box=1:boxcolor=black@0.75:boxborderw=15, '
        f'drawtext=text=\'WHAT HAPPENS IF YOU JUMP INTO JUPITER?\':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=280:box=1:boxcolor=black@0.85:boxborderw=18, '
        f'drawtext=text=\'NO SOLID GROUND!\':fontcolor=#FF3366:fontsize=60:x=(w-text_w)/2:y=1400:enable=\'between(t,3,9)\':box=1:boxcolor=black@0.85:boxborderw=20, '
        f'drawtext=text=\'PRESSURE CRUSHES EVERYTHING!\':fontcolor=#FFCC00:fontsize=52:x=(w-text_w)/2:y=1400:enable=\'between(t,9,16)\':box=1:boxcolor=black@0.85:boxborderw=20, '
        f'drawtext=text=\'SUBSCRIBE TO DAILY DOSE OF PHYSICS!\':fontcolor=#00FFFF:fontsize=48:x=(w-text_w)/2:y=1400:enable=\'between(t,16,{duration})\':box=1:boxcolor=black@0.85:boxborderw=20[outv]" '
        f'-map "[outv]" -map 1:a -c:v libx264 -preset fast -crf 20 -c:a aac -b:a 192k -shortest "What_Happens_If_You_Jump_Into_Jupiter.mp4"'
    )
    subprocess.run(ffmpeg_cmd, shell=True, check=True)
    print("Jupiter Short rendered successfully: What_Happens_If_You_Jump_Into_Jupiter.mp4")

if __name__ == "__main__":
    asyncio.run(generate_voice())
    render_short()
