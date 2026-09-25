import os
import re
import json
import urllib.request
import urllib.parse

def load_env_file():
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k not in os.environ:
                        os.environ[k] = v

def reengineer_with_gemini(raw_title, transcript):
    load_env_file()
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None

    prompt = f"""You are the lead scriptwriter for 'SciBytes', an elite viral space & science YouTube Shorts channel.
Analyze this viral reference video and rewrite it into an original, 100% unique, punchy 30-second YouTube Short.

Original Title: {raw_title}
Original Transcript:
{transcript}

CRITICAL RULES:
1. OPENING HOOK (0-3s): Start with a dramatic curiosity gap or shocking statement. Never say 'Hey guys' or 'Welcome back'.
2. PACING: Explain the mind-blowing science simply and with extreme awe. Keep it between 55 to 75 words (~25-30 seconds).
3. OUTRO: The very last sentence MUST be exactly: "Subscribe to SciBytes for more interesting videos!"
4. Return ONLY a valid JSON object with the following keys (no markdown code blocks, just raw JSON):
{{
  "title": "Short punchy title ending with #Shorts",
  "top_header": "CATEGORY BANNER (2-3 words uppercase)",
  "sub_header": "TOPIC SUBTITLE (3-5 words uppercase)",
  "script": "Complete spoken script for voiceover",
  "keywords": ["keyword1", "keyword2", "keyword3"]
}}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            text = data['candidates'][0]['content']['parts'][0]['text'].strip()
            # Clean markdown formatting if present
            if text.startswith('```'):
                text = re.sub(r'^```json\s*', '', text)
                text = re.sub(r'^```\s*', '', text)
                text = re.sub(r'```$', '', text).strip()
            return json.loads(text)
    except Exception as e:
        print(f"Notice: Gemini API re-engineer notice ({e}), using Heuristic AI Engine...")
        return None

def heuristic_reengineer(raw_title, transcript):
    """
    Intelligent heuristic rewriter that extracts key concepts, builds a viral curiosity hook,
    and formats for SciBytes without needing third-party API keys.
    """
    clean_title = re.sub(r'#\S+', '', raw_title).strip()
    clean_title = re.sub(r'\s*-\s*Science Facts.*', '', clean_title).strip()

    # Extract sentences
    raw_sentences = [s.strip() for s in re.split(r'[.!?]', transcript) if len(s.strip()) > 15]

    # Build viral hook
    if not raw_sentences:
        hook = f"Scientists have just uncovered something incredible about {clean_title}."
        body = f"This cosmic phenomenon reveals the extreme physics operating in deep space."
    else:
        # Take the most impactful sentence for the body
        hook_candidate = raw_sentences[0]
        if not hook_candidate.lower().startswith(('what', 'why', 'how', 'imagine', 'if')):
            hook = f"Did you know that {hook_candidate[0].lower() + hook_candidate[1:]}?"
        else:
            hook = hook_candidate + "."

        body = " ".join(raw_sentences[1:3])
        if not body:
            body = "This deep space discovery proves that reality in the cosmos is far stranger than fiction."

    full_script = f"{hook} {body}".strip()
    # Normalize ending
    full_script = re.sub(r'Subscribe.*$', '', full_script, flags=re.IGNORECASE).strip()
    full_script += " Subscribe to SciBytes for more interesting videos!"

    top_header = "COSMIC DISCOVERY"
    sub_header = clean_title.upper()[:35]

    return {
        "title": f"{clean_title} #Shorts",
        "top_header": top_header,
        "sub_header": sub_header,
        "script": full_script,
        "keywords": [clean_title, "space facts", "astronomy", "physics", "universe"]
    }

def reengineer_script(raw_title, transcript):
    res = reengineer_with_gemini(raw_title, transcript)
    if not res:
        res = heuristic_reengineer(raw_title, transcript)
    return res

if __name__ == '__main__':
    test_title = "Why Black Holes Warp Time"
    test_trans = "Near a black hole, gravity is so intense that time actually slows down compared to Earth. A clock placed on the event horizon would tick far slower than a clock on our wrist."
    result = reengineer_script(test_title, test_trans)
    print(json.dumps(result, indent=2))
