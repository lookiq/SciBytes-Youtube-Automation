import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
for p in (PROJECT_ROOT, SCRIPT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

# Color Psychology Mapping
# Yellow (#FFE600) -> Sun / Solar / Stars
# Red (#FF334B)    -> Black Holes / Singularities / Supernovas / Cosmic Dangers
# Cyan (#00E5FF)   -> Deep Space / Light / Quantum / James Webb / Galaxies
THEME_PALETTES = {
    'danger': {
        'tag_bg': (255, 51, 75, 245),       # Vibrant Red
        'tag_text': (255, 255, 255, 255),
        'accent_border': (255, 51, 75, 160),
        'glow': (255, 51, 75, 60),
        'default_tag': 'COSMIC DANGER'
    },
    'solar': {
        'tag_bg': (255, 230, 0, 245),       # Vibrant Yellow
        'tag_text': (10, 10, 10, 255),
        'accent_border': (255, 230, 0, 160),
        'glow': (255, 230, 0, 60),
        'default_tag': 'SOLAR PHENOMENON'
    },
    'space': {
        'tag_bg': (0, 229, 255, 245),       # Vibrant Cyan
        'tag_text': (10, 10, 10, 255),
        'accent_border': (0, 229, 255, 160),
        'glow': (0, 229, 255, 60),
        'default_tag': 'DEEP SPACE MYSTERY'
    }
}

def detect_color_psychology_theme(topic_text):
    text = topic_text.lower()
    if any(k in text for k in ['black hole', 'singularity', 'event horizon', 'destroy', 'crush', 'fall into', 'danger', 'supernova', 'explode', 'deadly', 'spaghetti']):
        return 'danger'
    elif any(k in text for k in ['sun', 'solar', 'flare', 'plasma', 'fire', 'heat', 'radiation', 'star', 'fusion']):
        return 'solar'
    else:
        return 'space'

def get_system_font(size, bold=True):
    font_candidates = [
        "C:/Windows/Fonts/ariblk.ttf",       # Arial Black
        "C:/Windows/Fonts/seguiui.ttf",      # Segoe UI
        "C:/Windows/Fonts/arialbd.ttf",      # Arial Bold
        "C:/Windows/Fonts/trebucbd.ttf",     # Trebuchet MS Bold
        "C:/Windows/Fonts/impact.ttf",       # Impact
    ]
    for fc in font_candidates:
        if os.path.exists(fc):
            try:
                return ImageFont.truetype(fc, size)
            except Exception:
                pass
    return ImageFont.load_default()

def create_top_hook_card(topic_title, category_tag=None, theme_key=None, dest_path=None):
    """
    Creates a high-end, glassmorphism Top Hook Card (Box 2)
    rendered on a transparent 1080x1920 canvas located in the upper 25%.
    """
    if not theme_key:
        theme_key = detect_color_psychology_theme(topic_title)
    theme = THEME_PALETTES.get(theme_key, THEME_PALETTES['space'])

    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Card geometry (Upper 25% zone)
    card_x0, card_y0 = 60, 95
    card_x1, card_y1 = 1020, 345
    card_w = card_x1 - card_x0
    card_h = card_y1 - card_y0

    # 1. Subtle drop shadow
    shadow_img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    s_draw.rounded_rectangle([card_x0, card_y0 + 8, card_x1, card_y1 + 8], radius=24, fill=(0, 0, 0, 180))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(16))
    img = Image.alpha_composite(shadow_img, img)
    draw = ImageDraw.Draw(img)

    # 2. Main Glassmorphism container
    draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=24, fill=(12, 14, 22, 215))

    # 3. Ambient inner border + top accent highlight
    draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=24, outline=(255, 255, 255, 45), width=2)
    draw.line([(card_x0 + 35, card_y0), (card_x1 - 35, card_y0)], fill=theme['accent_border'], width=4)

    # 4. Color Psychology Tag Badge
    tag_str = (category_tag or theme['default_tag']).upper()
    tag_font = get_system_font(26, bold=True)
    tag_bbox = draw.textbbox((0, 0), tag_str, font=tag_font)
    t_w = tag_bbox[2] - tag_bbox[0]
    t_h = tag_bbox[3] - tag_bbox[1]

    tag_x0 = card_x0 + 30
    tag_y0 = card_y0 + 24
    tag_x1 = tag_x0 + t_w + 32
    tag_y1 = tag_y0 + t_h + 14

    draw.rounded_rectangle([tag_x0, tag_y0, tag_x1, tag_y1], radius=10, fill=theme['tag_bg'])
    draw.text((tag_x0 + 16, tag_y0 + 7), tag_str, font=tag_font, fill=theme['tag_text'])

    # 5. Channel branding tag on top right
    brand_font = get_system_font(24, bold=True)
    brand_text = "SCIBYTES DAILY"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
    b_w = brand_bbox[2] - brand_bbox[0]
    draw.text((card_x1 - 30 - b_w, card_y0 + 28), brand_text, font=brand_font, fill=(180, 185, 200, 230))

    # 6. Main Hook Title Text (Word-wrapped with auto font-size fitting)
    clean_title = topic_title.replace('#Shorts', '').replace('#shorts', '').strip().upper()
    max_text_w = card_w - 70

    # Auto-fit font size
    chosen_size = 42
    title_font = get_system_font(chosen_size, bold=True)
    import textwrap
    lines = textwrap.wrap(clean_title, width=28)
    if len(lines) > 2:
        lines = textwrap.wrap(clean_title, width=34)
        chosen_size = 36
        title_font = get_system_font(chosen_size, bold=True)

    # Check if lines still exceed width
    for ln in lines:
        bb = draw.textbbox((0, 0), ln, font=title_font)
        if (bb[2] - bb[0]) > max_text_w:
            chosen_size = 32
            title_font = get_system_font(chosen_size, bold=True)
            break

    y_text = card_y0 + 82
    line_spacing = chosen_size + 14
    for idx, ln in enumerate(lines[:2]):
        y_curr = y_text + (idx * line_spacing)
        draw.text((card_x0 + 32, y_curr + 2), ln, font=title_font, fill=(0, 0, 0, 220))
        draw.text((card_x0 + 30, y_curr), ln, font=title_font, fill=(255, 255, 255, 255))

    if dest_path:
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
        img.save(dest_path, "PNG")
        print(f"Top Hook Card (Box 2) saved: {dest_path}")
    return img

def create_floating_subscribe_pill(dest_path=None):
    """
    Creates a floating YouTube Subscribe Pill Badge (Box 3)
    rendered on a transparent 1080x1920 canvas at the bottom safe zone.
    """
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pill_w = 460
    pill_h = 86
    pill_x0 = (1080 - pill_w) // 2
    pill_y0 = 1585
    pill_x1 = pill_x0 + pill_w
    pill_y1 = pill_y0 + pill_h

    # 1. Floating Shadow
    shadow_img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    s_draw.rounded_rectangle([pill_x0, pill_y0 + 6, pill_x1, pill_y1 + 6], radius=43, fill=(0, 0, 0, 210))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(14))
    img = Image.alpha_composite(shadow_img, img)
    draw = ImageDraw.Draw(img)

    # 2. YouTube Red Pill Container
    draw.rounded_rectangle([pill_x0, pill_y0, pill_x1, pill_y1], radius=43, fill=(225, 20, 35, 245))
    draw.rounded_rectangle([pill_x0, pill_y0, pill_x1, pill_y1], radius=43, outline=(255, 255, 255, 190), width=2)

    # 3. Inner White Play Triangle
    tri_x = pill_x0 + 40
    tri_y = pill_y0 + 27
    draw.polygon([(tri_x, tri_y), (tri_x + 22, tri_y + 16), (tri_x, tri_y + 32)], fill=(255, 255, 255, 255))

    # 4. Subscribe Text (Crisp Segoe UI / Arial Bold)
    sub_font = get_system_font(34, bold=True)
    draw.text((pill_x0 + 78, pill_y0 + 24), "SUBSCRIBE", font=sub_font, fill=(255, 255, 255, 255))

    # 5. Channel Name with clean separator
    handle_font = get_system_font(26, bold=True)
    draw.text((pill_x0 + 300, pill_y0 + 28), "| SciBytes", font=handle_font, fill=(255, 235, 235, 240))

    if dest_path:
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
        img.save(dest_path, "PNG")
        print(f"Floating Subscribe Pill Badge (Box 3) saved: {dest_path}")
    return img

if __name__ == '__main__':
    create_top_hook_card("What would happen if a BLACK HOLE appeared in your classroom", dest_path="temp/test_top_hook_card.png")
    create_floating_subscribe_pill(dest_path="temp/test_subscribe_pill.png")
