# scripts/generate_placeholder_images.py
"""
Generate placeholder images from image prompts using Pillow.
Saves to outputs/images/
"""
from PIL import Image, ImageDraw, ImageFont
import os, textwrap

ROOT = os.path.dirname(__file__)
OUT = os.path.join(ROOT, "..", "outputs", "images")
os.makedirs(OUT, exist_ok=True)

PROMPTS = [
    "Hero: Beautiful modern kitchen with bold accent wall, textured finish, Calyco paint",
    "Before-and-after: living room repaint, warm neutrals, washable finish (Calyco)"
]

def make_image(text, path, size=(1200,800), bg=(240,240,240)):
    img = Image.new("RGB", size, color=bg)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font = ImageFont.load_default()

    margin = 40
    wrapped = textwrap.fill(text, width=40)

    # Draw a rounded rectangle-like box (simple border)
    draw.rectangle([margin-10, margin-10, size[0]-margin+10, size[1]-margin+10], outline=(200,200,200), width=2)

    # Title text near top-left
    lines = wrapped.split("\n")
    y = margin + 10
    for line in lines:
        # Calculate text bbox for robust width/height measurement
        try:
            bbox = draw.textbbox((0,0), line, font=font)
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            # fallback for very old Pillow
            text_w, text_h = font.getsize(line)
        draw.text((margin, y), line, fill=(30,30,30), font=font)
        y += text_h + 8

    # Footer small note
    footer = "Image prompt: " + (text[:80] + "..." if len(text) > 80 else text)
    try:
        bbox = draw.textbbox((0,0), footer, font=font)
        fw = bbox[2] - bbox[0]
        fh = bbox[3] - bbox[1]
    except AttributeError:
        fw, fh = font.getsize(footer)

    draw.text((margin, size[1] - margin - fh), footer, fill=(90,90,90), font=font)
    img.save(path, quality=90)
    print("Saved placeholder image:", path)

def run():
    for i, p in enumerate(PROMPTS):
        fname = f"placeholder_{i+1}.jpg"
        path = os.path.join(OUT, fname)
        make_image(p, path)

if __name__ == "__main__":
    run()
