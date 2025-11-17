# pipeline/utils/images.py
import hashlib
import io
import os
from PIL import Image

def sha256_bytes(b: bytes) -> str:
    """Return sha256 hex digest for bytes."""
    return hashlib.sha256(b).hexdigest()

def is_valid_image(content: bytes) -> bool:
    """
    Return True if the given bytes appear to be a valid image PIL can open.
    """
    try:
        Image.open(io.BytesIO(content)).verify()
        return True
    except Exception:
        return False

def save_image_if_new(content: bytes, dest_folder: str, filename_hint: str, seen: dict) -> str:
    """
    Save image bytes to dest_folder using filename_hint (sanitized).
    Deduplicate by sha256 using 'seen' dict (sha256 -> saved_path).
    Returns the saved file path (string).
    """
    os.makedirs(dest_folder, exist_ok=True)
    digest = sha256_bytes(content)
    if digest in seen:
        return seen[digest]

    # sanitize filename hint
    safe_name = "".join(c for c in filename_hint if c.isalnum() or c in (" ", ".", "_", "-")).strip()
    if not safe_name:
        safe_name = f"image_{digest[:8]}.jpg"
    # ensure an extension
    if "." not in safe_name:
        safe_name = safe_name + ".jpg"

    base = os.path.join(dest_folder, safe_name)
    out_path = base
    i = 1
    while os.path.exists(out_path):
        name, ext = os.path.splitext(base)
        out_path = f"{name}_{i}{ext}"
        i += 1

    with open(out_path, "wb") as f:
        f.write(content)

    seen[digest] = out_path
    return out_path
