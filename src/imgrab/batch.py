"""Batch download command."""

import sys
import time
import asyncio
from pathlib import Path
from urllib.parse import urlparse, unquote
import os

import click
import httpx

from imgrab.output import resolve_output_path, save_image_bytes
from imgrab.utils import USER_AGENT, log_verbose, log_error


async def _download_one(client, url, output_dir, fmt, force, verbose, quiet):
    """Download a single image. Returns (url, success, error_msg)."""
    try:
        resp = await client.get(url)
        if resp.status_code >= 400:
            return (url, False, f"HTTP {resp.status_code}")

        content_type = resp.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            return (url, False, f"Not an image: {content_type}")

        parsed = urlparse(url)
        filename = unquote(os.path.basename(parsed.path)) or "image"
        if not Path(filename).suffix and fmt:
            filename = f"{filename}.{fmt}"
        elif not Path(filename).suffix:
            ext = content_type.split("/")[-1].split(";")[0].replace("jpeg", "jpg")
            filename = f"{filename}.{ext}"

        dest = resolve_output_path(str(output_dir / filename), fmt, force)
        save_image_bytes(resp.content, dest, fmt)
        return (url, True, str(dest))
    except Exception as e:
        return (url, False, str(e))


async def _batch_download(urls, output_dir, fmt, force, concurrency, verbose, quiet):
    """Download all URLs with concurrency limit."""
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async with httpx.AsyncClient(follow_redirects=True, max_redirects=10, timeout=30.0,
                                  headers={"User-Agent": USER_AGENT}) as client:
        async def _limited(url):
            async with semaphore:
                return await _download_one(client, url, output_dir, fmt, force, verbose, quiet)

        results = await asyncio.gather(*[_limited(u) for u in urls])

    return results


@click.command("batch")
@click.argument("file", type=click.Path(exists=True))
@click.option("-o", "--output", "output_dir", default=".", help="Output directory.")
@click.option("--format", "fmt", type=click.Choice(["png", "jpg", "webp", "gif"], case_sensitive=False), help="Convert to format.")
@click.option("--concurrency", type=click.IntRange(1, 16), default=4, help="Concurrent downloads (1-16).")
@click.option("--force", is_flag=True, help="Overwrite existing files.")
@click.pass_context
def batch_cmd(ctx, file, output_dir, fmt, concurrency, force):
    """Download images from a file containing one URL per line.

    Example: imgrab batch urls.txt -o ./assets/ --concurrency 8
    """
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    start = time.time()

    # Read and parse URLs
    try:
        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        log_error(f"Error: Cannot read file '{file}': {e}")
        sys.exit(1)

    urls = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)

    if not urls:
        if not quiet:
            click.echo("No URLs found in file.")
        return

    log_verbose(verbose, quiet, f"Batch: {len(urls)} URLs, concurrency={concurrency}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Run async downloads
    results = asyncio.run(_batch_download(urls, out_dir, fmt, force, concurrency, verbose, quiet))

    success_count = sum(1 for _, ok, _ in results if ok)
    fail_count = sum(1 for _, ok, _ in results if not ok)

    # Log failures to stderr
    for url, ok, msg in results:
        if not ok:
            log_verbose(verbose, quiet, f"  FAIL: {url} - {msg}")
            if not quiet:
                click.echo(f"  FAIL: {url} - {msg}", err=True)

    elapsed = time.time() - start

    if not quiet:
        click.echo(f"✓ {success_count} downloaded, {fail_count} failed ({elapsed:.1f}s)")
