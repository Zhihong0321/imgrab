"""Windows clipboard integration."""

import io
import sys


def copy_to_clipboard(image_bytes: bytes) -> bool:
    """Copy image bytes to Windows clipboard as a bitmap. Returns True on success."""
    try:
        import win32clipboard
        from PIL import Image

        # Convert to BMP for clipboard
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode == "RGBA":
            # Clipboard doesn't handle alpha well, composite on white
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # For animated images, use first frame only
        if hasattr(img, "n_frames") and img.n_frames > 1:
            img.seek(0)

        # Convert to BMP bytes (skip BMP header for clipboard)
        output = io.BytesIO()
        img.save(output, format="BMP")
        bmp_data = output.getvalue()[14:]  # Skip BMP file header

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
        win32clipboard.CloseClipboard()
        return True

    except ImportError:
        print("Warning: pywin32 not installed. Clipboard not available.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Warning: Clipboard error: {e}", file=sys.stderr)
        return False
