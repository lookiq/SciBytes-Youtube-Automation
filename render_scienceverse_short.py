import asyncio
import subprocess
import edge_tts

SCRIPT = (
    "When a heat-seeking missile locks onto a fighter jet, the pilot has less than four seconds to react. "
    "These missiles don't chase the jet itself—they hunt the blazing one thousand degree heat from the engine. "
    "To survive, pilots deploy flares. These burning pellets ignite at over two thousand degrees Celsius, "
    "tricking the missile into chasing a decoy and exploding harmlessly in mid-air. "
    "Subscribe to Daily Dose of Physics for more insane science!"
)

async def generate_voice():
    print("Generating Scienceverse documentary voice...")
    communicate = edge_tts.Communicate(SCRIPT, "en-US-ChristopherNeural", rate="+5%")
    await communicate.save("jet_voice.mp3")
    print("Voice generated: jet_voice.mp3")

def render_video():
    ffprobe_cmd = 'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 jet_voice.mp3'
    duration = float(subprocess.check_output(ffprobe_cmd, shell=True, text=True).strip())
    print(f"Voice duration: {duration:.2f}s")

    # Scienceverse-style 9:16 vertical broadcast layout
    ffmpeg_cmd = (
        f'ffmpeg -y -ss 2 -i jet_clip.mp4.mkv -i jet_voice.mp3 '
        f'-filter_complex "'
        f'[0:v]trim=duration={duration},setpts=PTS-STARTPTS,split=2[orig1][orig2]; '
        f'[orig1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:10,eq=brightness=-0.15[bg]; '
        f'[orig2]scale=1080:-1[fg]; '
        f'[bg][fg]overlay=0:(1920-overlay_h)/2[vid]; '
        f'[vid]drawtext=text=\'SCIENCEVERSE STYLE\':fontcolor=#FFCC00:fontsize=40:x=(w-text_w)/2:y=170:box=1:boxcolor=black@0.8:boxborderw=14, '
        f'drawtext=text=\'HOW FIGHTER JETS DODGE MISSILES\':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=270:box=1:boxcolor=black@0.85:boxborderw=18, '
        f'drawtext=text=\'LESS THAN 4 SECONDS TO REACT!\':fontcolor=#FFFFFF:fontsize=54:x=(w-text_w)/2:y=1380:enable=\'between(t,0,5)\':box=1:boxcolor=red@0.9:boxborderw=20, '
        f'drawtext=text=\'HEAT-SEEKING INFRARED MISSILE!\':fontcolor=#FFFF00:fontsize=50:x=(w-text_w)/2:y=1380:enable=\'between(t,5,11)\':box=1:boxcolor=black@0.9:boxborderw=20, '
        f'drawtext=text=\'FLARES BURN AT 2000°C!\':fontcolor=#FF3366:fontsize=56:x=(w-text_w)/2:y=1380:enable=\'between(t,11,17)\':box=1:boxcolor=black@0.9:boxborderw=20, '
        f'drawtext=text=\'SUBSCRIBE FOR MORE CRAZY SCIENCE!\':fontcolor=#00FFFF:fontsize=46:x=(w-text_w)/2:y=1380:enable=\'between(t,17,{duration})\':box=1:boxcolor=black@0.9:boxborderw=20[outv]" '
        f'-map "[outv]" -map 1:a -c:v libx264 -preset fast -crf 20 -c:a aac -b:a 192k -shortest "How_Fighter_Jets_Dodge_Missiles.mp4"'
    )
    print("Rendering video with FFmpeg...")
    subprocess.run(ffmpeg_cmd, shell=True, check=True)
    print("Video rendered successfully: How_Fighter_Jets_Dodge_Missiles.mp4")

if __name__ == "__main__":
    asyncio.run(generate_voice())
    render_video()
