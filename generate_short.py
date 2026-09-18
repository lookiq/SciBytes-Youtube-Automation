import os
import json
import asyncio
import edge_tts
from google import genai
from google.genai import types

API_KEY = "AQ.Ab8RN6LcOVzyBzej9tLbpqE0L2Vfu3CrDc1ujEksnSXUUa7rYg"
client = genai.Client(api_key=API_KEY)

def generate_script(topic="What happens if you fall into a Black Hole?"):
    prompt = f"""You are the head scriptwriter for the YouTube Shorts channel "Daily Dose of Physics" (@dailyphysicsforyou).
Write a high-retention, mind-blowing 30-40 second YouTube Short script about: "{topic}".

Rules:
1. The first 3 seconds MUST have an irresistible psychological HOOK that prevents scrolling.
2. Fast-paced, fascinating, scientifically accurate yet easy to understand.
3. End with a strong mind-bending statement and CTA: "Subscribe to Daily Dose of Physics for more mind-bending science!"
4. Return ONLY a valid JSON object with this exact structure:
{{
  "title": "Catchy YouTube Shorts Title with emojis (under 60 chars)",
  "hook": "First 3-second hook sentence",
  "full_script": "The complete narration script for the voiceover without stage directions",
  "description": "Engaging description with emojis and tags",
  "tags": ["#DailyDoseOfPhysics", "#Physics", "#BlackHole", "#SpaceFacts", "#Shorts", "#Science"]
}}
"""
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    return json.loads(response.text)

async def generate_voiceover(text, output_path="temp_audio.mp3"):
    voice = "en-US-ChristopherNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    print(f"Voiceover saved to: {output_path}")

if __name__ == "__main__":
    print("Generating script with Gemini...")
    script_data = generate_script()
    print("\n--- GENERATED SCRIPT ---")
    print("Title:", script_data["title"])
    print("Hook:", script_data["hook"])
    print("Full Script:\n", script_data["full_script"])
    
    with open("latest_script.json", "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2, ensure_ascii=False)
        
    print("\nGenerating AI Narration...")
    asyncio.run(generate_voiceover(script_data["full_script"], "latest_voice.mp3"))
    print("\nAll done successfully!")
