"""Direct HTTP image download command."""

import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, unquote

import click
import httpx

from imgrab.clipboard import copy_to_clipboard
from imgrab.output import resolve_output_path, save_image_bytes
from imgrab.utils import USER_AGENT, log_verbose, log_error, IMAGE_CONTENT_TYPES


@click.command("download")
@click.argument("url")
@click.option("-o", "--output", "output_path", default=None, help="Output file path.")
@click.option("--format", "fmt", type=click.Choice(["png", "jpg", "webp", "gif"], case_sensitive=False), help="Convert to format.")
@click.option("--header", "headers", multiple=True, help="Custom header as 'Key: Value'. Repeatable.")
@click.option("--clipboard", "to_clipboard", is_flag=True, help="Copy image to Windows clipboard.")
@click.option("--force", is_flag=True, help="Overwrite existing files.")
@click.pass_context
def download_cmd(ctx, url, output_path, fmt, headers, to_clipboard, force):
    """Download an image directly from a URL.

    Example: imgrab download https://example.com/photo.jpg -o ./assets/photo.png
    """
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    # Parse custom headers
    custom_headers = {"User-Agent": USER_AGENT}
    for h in headers:
        if ":" in h:
            key, value = h.split(":", 1)
            custom_headers[key.strip()] = value.strip()

    start = time.time()
    log_verbose(verbose, quiet, f"Downloading: {url}")

    try:
        with httpx.Client(follow_redirects=True, max_redirects=10, timeout=30.0) as client:
            response = client.get(url, headers=custom_headers)
    except httpx.TooManyRedirects:
        log_error("Error: Too many redirects (limit: 10).")
        sys.exit(1)
    except httpx.TimeoutException:
        log_error(f"Error: Connection timed out for {url}")
        sys.exit(1)
    except httpx.RequestError as e:
        log_error(f"Error: Network error - {e}")
        sys.exit(1)

    # Check HTTP status
    if response.status_code == 403 or response.status_code == 429:
        log_error(f"Error: HTTP {response.status_code}. Try: imgrab screenshot {url}")
        sys.exit(1)
    elif response.status_code >= 400:
        log_error(f"Error: HTTP {response.status_code}")
        sys.exit(1)

    # Validate content type
    content_type = response.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        log_error(f"Error: URL does not point to an image (Content-Type: {content_type})")
        sys.exit(1)

    image_data = response.content

    # Determine output path
    if output_path is None:
        parsed = urlparse(url)
        filename = unquote(os.path.basename(parsed.path)) or "image"
        if not Path(filename).suffix and fmt:
            filename = f"{filename}.{fmt}"
        elif not Path(filename).suffix:
            # Derive from content-type
            ext = content_type.split("/")[-1].split(";")[0]
            ext = ext.replace("jpeg", "jpg")
            filename = f"{filename}.{ext}"
        output_path = filename

    dest = resolve_output_path(output_path, fmt, force)
    save_image_bytes(image_data, dest, fmt)

    elapsed = time.time() - start
    log_verbose(verbose, quiet, f"Saved: {dest} ({elapsed:.1f}s)")

    if to_clipboard:
        success = copy_to_clipboard(image_data)
        if success:
            log_verbose(verbose, quiet, "Copied to clipboard.")
        else:
            log_error("Error: Failed to copy to clipboard.")
            if not dest.exists():
                sys.exit(1)

    if not quiet:
        click.echo(f"✓ {dest}")
