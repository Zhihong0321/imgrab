"""Search for images using Gemini CLI and download them."""

import os
import re
import sys
import time
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse, unquote

import click
import httpx

from imgrab.clipboard import copy_to_clipboard
from imgrab.output import resolve_output_path, save_image_bytes
from imgrab.utils import USER_AGENT, log_verbose, log_error

# Known image-hosting domains
IMAGE_HOSTS = {
    "i.imgur.com", "images.unsplash.com", "pbs.twimg.com",
    "upload.wikimedia.org", "cdn.pixabay.com", "images.pexels.com",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff"}

URL_PATTERN = re.compile(r'https?://[^\s<>"\'\]\)]+')


def _is_image_url(url: str) -> bool:
    """Check if a URL looks like a direct image link."""
    parsed = urlparse(url)
    path_lower = parsed.path.lower().rstrip("/")
    # Check extension
    for ext in IMAGE_EXTENSIONS:
        if path_lower.endswith(ext):
            return True
    # Check known image hosts
    if parsed.hostname and parsed.hostname in IMAGE_HOSTS:
        return True
    return False


def _build_prompt(query: str, limit: int) -> str:
    """Build the prompt for Gemini CLI."""
    return (
        f"Find {limit} direct image file URLs for: {query}\n\n"
        "Requirements:\n"
        "- Return ONLY direct URLs to image files (ending in .jpg, .jpeg, .png, .gif, .webp)\n"
        "- Do NOT return web page URLs that contain images\n"
        "- Do NOT return search engine result page URLs\n"
        "- Return one URL per line, plain text, no markdown, no numbering, no extra text\n"
        "- URLs must be real, publicly accessible image file URLs\n"
    )


def _run_gemini(prompt: str, timeout: int) -> str:
    """Run Gemini CLI with the given prompt. Returns stdout."""
    try:
        env = os.environ.copy()
        env["GEMINI_CLI_TRUST_WORKSPACE"] = "true"
        result = subprocess.run(
            ["gemini", "-p", prompt],
            shell=True,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        log_error("Error: Gemini CLI not found. Install it: https://github.com/google-gemini/gemini-cli")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        log_error(f"Error: Gemini CLI timed out after {timeout}s")
        sys.exit(1)

    if result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else "Unknown error"
        log_error(f"Error: Gemini CLI failed: {stderr}")
        sys.exit(1)

    return result.stdout


def _extract_urls(output: str, limit: int) -> list[str]:
    """Extract and deduplicate image URLs from Gemini output."""
    all_urls = URL_PATTERN.findall(output)
    seen = set()
    image_urls = []
    for url in all_urls:
        # Clean trailing punctuation
        url = url.rstrip(".,;:!?)")
        if url in seen:
            continue
        if _is_image_url(url):
            seen.add(url)
            image_urls.append(url)
            if len(image_urls) >= limit:
                break
    return image_urls


@click.command("search")
@click.argument("query")
@click.option("--limit", type=click.IntRange(1, 50), default=5, help="Max number of images to find (1-50).")
@click.option("-o", "--output", "output_dir", default=".", help="Output directory for downloads.")
@click.option("--format", "fmt", type=click.Choice(["png", "jpg", "webp", "gif"], case_sensitive=False), help="Convert to format.")
@click.option("--concurrency", type=click.IntRange(1, 16), default=4, help="Concurrent downloads (1-16).")
@click.option("--timeout", type=click.IntRange(10, 300), default=60, help="Gemini CLI timeout in seconds.")
@click.option("--yes", "-y", "auto_yes", is_flag=True, help="Skip download confirmation.")
@click.option("--no-download", is_flag=True, help="Only list URLs, don't download.")
@click.option("--clipboard", "to_clipboard", is_flag=True, help="Copy first image to clipboard.")
@click.option("--force", is_flag=True, help="Overwrite existing files.")
@click.pass_context
def search_cmd(ctx, query, limit, output_dir, fmt, concurrency, timeout, auto_yes, no_download, to_clipboard, force):
    """Search for images using Gemini CLI and download them.

    Example: imgrab search "cat playing piano" -o ./assets/ --limit 5
    """
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    start = time.time()

    # Verify gemini is available
    if not shutil.which("gemini"):
        log_error("Error: Gemini CLI not found on PATH. Install: https://github.com/google-gemini/gemini-cli")
        sys.exit(1)

    # Build and run prompt
    prompt = _build_prompt(query, limit)
    log_verbose(verbose, quiet, f"Searching: {query} (limit={limit}, timeout={timeout}s)")

    output = _run_gemini(prompt, timeout)
    log_verbose(verbose, quiet, f"Gemini responded ({time.time() - start:.1f}s)")

    # Extract URLs
    image_urls = _extract_urls(output, limit)

    if not image_urls:
        if not quiet:
            click.echo("No images found for query.")
        sys.exit(0)

    # Display results
    if not quiet:
        click.echo(f"Found {len(image_urls)} image(s):")
        for i, url in enumerate(image_urls, 1):
            click.echo(f"  {i}. {url}")

    if no_download:
        return

    # Confirm download
    if not auto_yes:
        confirm = click.prompt("Download? [y/N]", default="n")
        if confirm.lower() not in ("y", "yes"):
            if not quiet:
                click.echo("Skipped.")
            return

    # Download
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    fail_count = 0
    first_image_data = None

    with httpx.Client(follow_redirects=True, max_redirects=10, timeout=30.0,
                      headers={"User-Agent": USER_AGENT}) as client:
        for img_url in image_urls:
            try:
                resp = client.get(img_url)
                if resp.status_code >= 400:
                    fail_count += 1
                    log_verbose(verbose, quiet, f"  FAIL: {img_url} (HTTP {resp.status_code})")
                    click.echo(f"  FAIL: {img_url} - HTTP {resp.status_code}", err=True)
                    continue

                parsed = urlparse(img_url)
                filename = unquote(os.path.basename(parsed.path)) or "image"
                dest = resolve_output_path(str(out_dir / filename), fmt, force)
                save_image_bytes(resp.content, dest, fmt)
                success_count += 1
                log_verbose(verbose, quiet, f"  OK: {dest}")

                if first_image_data is None:
                    first_image_data = resp.content

            except Exception as e:
                fail_count += 1
                click.echo(f"  FAIL: {img_url} - {e}", err=True)

    elapsed = time.time() - start

    if not quiet:
        click.echo(f"Done: {success_count} downloaded, {fail_count} failed ({elapsed:.1f}s)")

    # Clipboard
    if to_clipboard and first_image_data:
        success = copy_to_clipboard(first_image_data)
        if success:
            log_verbose(verbose, quiet, "Copied first image to clipboard.")
        else:
            log_error("Error: Failed to copy to clipboard.")
            sys.exit(1)



