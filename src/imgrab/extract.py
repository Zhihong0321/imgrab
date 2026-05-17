"""Page image extraction command."""

import sys
import time

import click

from imgrab.utils import log_verbose, log_error


@click.command("extract")
@click.argument("url")
@click.option("-o", "--output", "output_dir", default=None, help="Output directory for downloaded images.")
@click.option("--selector", default=None, help="CSS selector to limit extraction scope.")
@click.option("--download", "do_download", is_flag=True, help="Download all extracted images.")
@click.option("--format", "fmt", type=click.Choice(["png", "jpg", "webp", "gif"], case_sensitive=False), help="Convert downloaded images to format.")
@click.option("--force", is_flag=True, help="Overwrite existing files.")
@click.pass_context
def extract_cmd(ctx, url, output_dir, selector, do_download, fmt, force):
    """Extract all image URLs from a web page.

    Example: imgrab extract https://example.com/gallery --download -o ./images/
    """
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    start = time.time()
    log_verbose(verbose, quiet, f"Extracting images from: {url}")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log_error("Error: playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, wait_until="networkidle", timeout=30000)

            # Extract image URLs
            image_urls = page.evaluate("""(selector) => {
                const urls = new Set();
                const scope = selector ? document.querySelectorAll(selector) : [document];

                for (const root of scope) {
                    // img src
                    const imgs = root.querySelectorAll ? root.querySelectorAll('img[src]') : document.querySelectorAll('img[src]');
                    imgs.forEach(img => {
                        if (img.src) urls.add(img.src);
                        if (img.srcset) {
                            img.srcset.split(',').forEach(s => {
                                const u = s.trim().split(/\\s+/)[0];
                                if (u) urls.add(new URL(u, document.baseURI).href);
                            });
                        }
                    });

                    // CSS background-image
                    const allEls = root.querySelectorAll ? root.querySelectorAll('*') : document.querySelectorAll('*');
                    allEls.forEach(el => {
                        const bg = getComputedStyle(el).backgroundImage;
                        if (bg && bg !== 'none') {
                            const match = bg.match(/url\\(["']?(.+?)["']?\\)/);
                            if (match && match[1]) urls.add(new URL(match[1], document.baseURI).href);
                        }
                    });
                }

                return [...urls];
            }""", selector)

            browser.close()

    except Exception as e:
        error_msg = str(e)
        if "Timeout" in error_msg or "timeout" in error_msg:
            log_error(f"Error: Page load timed out (30s limit): {url}")
        else:
            log_error(f"Error: {error_msg}")
        sys.exit(1)

    if selector and not image_urls:
        log_error(f"Error: No elements match selector '{selector}'")
        sys.exit(1)

    if not image_urls:
        if not quiet:
            click.echo("No images found on page.")
        return

    log_verbose(verbose, quiet, f"Found {len(image_urls)} images")

    if do_download:
        import os
        from pathlib import Path
        from urllib.parse import urlparse, unquote
        import httpx
        from imgrab.output import resolve_output_path, save_image_bytes
        from imgrab.utils import USER_AGENT

        out_dir = Path(output_dir) if output_dir else Path(".")
        out_dir.mkdir(parents=True, exist_ok=True)

        success_count = 0
        fail_count = 0

        with httpx.Client(follow_redirects=True, max_redirects=10, timeout=30.0,
                          headers={"User-Agent": USER_AGENT}) as client:
            for img_url in image_urls:
                try:
                    resp = client.get(img_url)
                    if resp.status_code >= 400:
                        fail_count += 1
                        log_verbose(verbose, quiet, f"  FAIL: {img_url} (HTTP {resp.status_code})")
                        continue

                    parsed = urlparse(img_url)
                    filename = unquote(os.path.basename(parsed.path)) or "image"
                    dest = resolve_output_path(str(out_dir / filename), fmt, force)
                    save_image_bytes(resp.content, dest, fmt)
                    success_count += 1
                    log_verbose(verbose, quiet, f"  OK: {dest}")
                except Exception as e:
                    fail_count += 1
                    log_verbose(verbose, quiet, f"  FAIL: {img_url} ({e})")

        elapsed = time.time() - start
        if not quiet:
            click.echo(f"✓ {success_count} downloaded, {fail_count} failed ({elapsed:.1f}s)")
    else:
        # Just print URLs
        for img_url in image_urls:
            click.echo(img_url)
