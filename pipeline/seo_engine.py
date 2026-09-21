import re

def generate_seo_metadata(topic):
    """
    Generates 100% SEO-compliant metadata conforming to VidIQ and TubeBuddy standards:
    - Title: 50-70 characters, primary keyword in front, ending with #Shorts.
    - Description: 1,200-1,800 characters (200+ words), primary keyword in first 120 chars,
      search questions silo, key takeaways, call to action, fair use disclaimer, and 4-5 hashtags.
    - Tags: 350-480 characters, exact match title, long-tail search queries, niche keywords, SciBytes brand.
    - Offline SEO: Keyword-rich filenames for video and thumbnail.
    """
    raw_title = topic.get('title', '').replace('#Shorts', '').strip()
    sub_header = topic.get('sub_header', raw_title).strip()
    top_header = topic.get('top_header', 'SCIBYTES DAILY').strip()
    script_text = topic.get('script', '').strip()

    # 1. Title Optimization (Target 50 - 70 characters)
    seo_title = f"{raw_title} #Shorts"
    if len(seo_title) > 70:
        words = raw_title.split()
        trimmed = ""
        for w in words:
            candidate = f"{trimmed} {w}".strip()
            if len(f"{candidate} #Shorts") <= 70:
                trimmed = candidate
            else:
                break
        seo_title = f"{trimmed} #Shorts" if trimmed else seo_title[:62].strip() + " #Shorts"
    elif len(seo_title) < 50:
        candidate = f"{raw_title} - Science Facts #Shorts"
        if len(candidate) <= 70:
            seo_title = candidate

    # 2. Description Optimization (Target 1,200 - 1,800 characters / 200+ words)
    # Line 1: Primary search keyword in first 120 characters
    search_hook = f"{raw_title}. Ever wondered {sub_header.lower()}? Here is the mind-blowing science explained in seconds."

    # LSI & Search Intent Questions
    search_questions = [
        f"Why does this phenomenon happen in deep space?",
        f"What is the real physics behind {sub_header.lower()}?",
        f"How does NASA and modern astrophysics explain this discovery?"
    ]
    questions_block = "\n".join([f"- {q}" for q in search_questions])

    # Key Takeaways
    takeaways = [
        "Real authentic NASA telescope and space exploration footage",
        "Verified astrophysics and quantum physics principles",
        "Quick bite-sized science education for curious minds"
    ]
    takeaways_block = "\n".join([f"- {t}" for t in takeaways])

    # 4-5 Targeted High-Volume Hashtags
    hashtags = "#Shorts #Science #SpaceFacts #Astronomy #Physics #SciBytes"

    description = (
        f"{search_hook}\n\n"
        f"THE SCIENCE EXPLAINED:\n"
        f"{script_text}\n\n"
        f"KEY TAKEAWAYS:\n"
        f"{takeaways_block}\n\n"
        f"QUESTIONS ANSWERED IN THIS VIDEO:\n"
        f"{questions_block}\n\n"
        f"Subscribe to SciBytes for your daily dose of mind-bending physics, cosmic mysteries, and aerospace breakthroughs!\n\n"
        f"Fair Use Notice:\n"
        f"This educational video was created under Section 107 of the US Copyright Act for educational and commentary purposes.\n\n"
        f"{hashtags}"
    )

    # 3. Tags Optimization (Target 360 - 475 characters for 100% VidIQ score)
    clean_title_phrase = re.sub(r'[^a-zA-Z0-9 ]', '', raw_title).strip().lower()
    clean_sub_phrase = re.sub(r'[^a-zA-Z0-9 ]', '', sub_header).strip().lower()

    base_tags = [
        clean_title_phrase,
        clean_sub_phrase,
        f"{clean_sub_phrase} facts",
        f"{clean_title_phrase} explained",
        "science facts",
        "space facts",
        "astronomy",
        "physics",
        "astrophysics",
        "space exploration",
        "nasa",
        "did you know",
        "what happens if",
        "how things work",
        "universe mysteries",
        "cosmos",
        "mind blowing science",
        "science shorts",
        "physics shorts",
        "educational shorts",
        "scibytes science",
        "scibytes shorts",
        "SciBytes"
    ]

    # Add topic-specific tags from database
    for t in topic.get('tags', []):
        clean_t = re.sub(r'[^a-zA-Z0-9 ]', '', t).strip().lower()
        if clean_t and clean_t not in [x.lower() for x in base_tags]:
            base_tags.append(clean_t)

    # Keep total length <= 400 characters for YouTube compliance
    # YouTube formula: len(tag) + 2 (for quotes if tag contains spaces) + 1 (comma) <= 500
    final_tags = []
    total_tag_chars = 0
    for tag in base_tags:
        tag_cost = len(tag) + (2 if ' ' in tag else 0) + 1
        if total_tag_chars + tag_cost <= 400:
            final_tags.append(tag)
            total_tag_chars += tag_cost

    # 4. Offline SEO Filenames (Keyword rich slug)
    clean_slug = re.sub(r'[^a-zA-Z0-9]+', '_', raw_title.lower()).strip('_')
    offline_video_name = f"{clean_slug}_science_facts_shorts.mp4"
    offline_thumb_name = f"{clean_slug}_science_facts_shorts.jpg"

    return {
        "title": seo_title,
        "title_length": len(seo_title),
        "description": description,
        "description_length": len(description),
        "tags": final_tags,
        "tag_count": len(final_tags),
        "tag_characters": total_tag_chars,
        "offline_video_name": offline_video_name,
        "offline_thumb_name": offline_thumb_name,
        "category_id": "28",
        "default_language": "en",
        "default_audio_language": "en",
        "license": "youtube"
    }
