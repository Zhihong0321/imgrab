"""Output path resolution and image saving utilities."""

import io
from pathlib import Path

from PIL import Image


def resolve_output_path(output_path: str, fmt: str | None, force: bool) -> Path:
    """Resolve the final output path, handling directories, extensions, and conflicts."""
    dest = Path(output_path)

    # Create parent directories if needed
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Add extension if missing
    if not dest.suffix and fmt:
        ext = fmt if fmt != "jpg" else "jpg"
        dest = dest.with_suffix(f".{ext}")

    # Handle file conflicts
    if not force and dest.exists():
        stem = dest.stem
        suffix = dest.suffix
        parent = dest.parent
        for i in range(1, 100):
            candidate = parent / f"{stem}_{i}{suffix}"
            if not candidate.exists():
                dest = candidate
                break

    return dest


def save_image_bytes(data: bytes, dest: Path, fmt: str | None) -> None:
    """Save image bytes to disk, optionally converting format."""
    if fmt:
        # Convert format
        img = Image.open(io.BytesIO(data))
        pil_format = fmt.upper()
        if pil_format == "JPG":
            pil_format = "JPEG"

        if pil_format == "JPEG" and img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif pil_format == "JPEG" and img.mode != "RGB":
            img = img.convert("RGB")

        img.save(dest, format=pil_format)
    else:
        # Save raw bytes
        dest.write_bytes(data)
