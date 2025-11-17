# pipeline/image_generator.py
import os, json, base64
from pathlib import Path
from hashlib import sha1
from datetime import datetime
from PIL import Image
try:
    import openai
except Exception:
    openai = None

IMAGES_DIR = Path("images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
METADATA_PATH = IMAGES_DIR / "metadata.json"
if not METADATA_PATH.exists():
    METADATA_PATH.write_text("[]")

def _slug(prompt: str) -> str:
    h = sha1(prompt.encode("utf-8")).hexdigest()[:10]
    safe = "".join(c if c.isalnum() else "-" for c in prompt)[:40]
    return f"{safe}-{h}"

def _write_black(path: Path, size=(1024,1024)) -> str:
    img = Image.new("RGB", size, (0, 0, 0))
    img.save(path, "PNG")
    return str(path)

def _append_metadata(record: dict):
    try:
        data = json.loads(METADATA_PATH.read_text())
    except Exception:
        data = []
    data.append(record)
    METADATA_PATH.write_text(json.dumps(data, indent=2))

def generate_image(prompt: str, size: str = "1024x1024") -> str:
    filename = _slug(prompt) + f"-{size.replace('x','_')}.png"
    out_path = IMAGES_DIR / filename

    # if cached, return
    if out_path.exists():
        return str(out_path)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or openai is None:
        # placeholder
        size_tuple = (1024,1792) if "1792" in size else (1024,1024)
        created = _write_black(out_path, size_tuple)
        _append_metadata({"file": out_path.name, "prompt": prompt, "size": size, "mode": "placeholder", "ts": datetime.utcnow().isoformat()})
        return created

    try:
        openai.api_key = api_key
        resp = openai.images.generate(model="gpt-image-1", prompt=prompt, size=size, n=1)
        b64 = resp.data[0].b64_json
        img_bytes = base64.b64decode(b64)
        with open(out_path, "wb") as f:
            f.write(img_bytes)
        meta = {"file": out_path.name, "prompt": prompt, "size": size, "mode": "generated", "ts": datetime.utcnow().isoformat()}
        try:
            meta["api_id"] = resp.data[0].id
        except Exception:
            pass
        _append_metadata(meta)
        return str(out_path)
    except Exception as e:
        # fallback placeholder on any error
        size_tuple = (1024,1792) if "1792" in size else (1024,1024)
        created = _write_black(out_path, size_tuple)
        _append_metadata({"file": out_path.name, "prompt": prompt, "size": size, "mode": "error_fallback", "error": str(e), "ts": datetime.utcnow().isoformat()})
        return created
