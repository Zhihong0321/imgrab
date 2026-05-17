"""Browser screenshot capture command."""

import sys
import time
from pathlib import Path

import click

from imgrab.clipboard import copy_to_clipboard
from imgrab.output import resolve_output_path, save_image_bytes
from imgrab.utils import log_verbose, log_error


@click.command("screenshot")
@click.argument("url")
@click.option("-o", "--output", "output_path", default=None, help="Output file path.")
@click.option("--selector", default=None, help="CSS selector to capture a specific element.")
@click.option("--format", "fmt", type=click.Choice(["png", "jpg", "webp"], case_sensitive=False), default="png", help="Output format.")
@click.option("--clipboard", "to_clipboard", is_flag=True, help="Copy screenshot to Windows clipboard.")
@click.option("--force", is_flag=True, help="Overwrite existing files.")
@click.pass_context
def screenshot_cmd(ctx, url, output_path, selector, fmt, to_clipboard, force):
    """Capture a screenshot of a page or element via headless browser.

    Example: imgrab screenshot https://example.com/gallery --selector "img.hero" -o hero.png
    """
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    start = time.time()
    log_verbose(verbose, quiet, f"Screenshot: {url}")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log_error("Error: playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 720})

            log_verbose(verbose, quiet, "Loading page...")
            page.goto(url, wait_until="networkidle", timeout=30000)

            if selector:
                log_verbose(verbose, quiet, f"Finding element: {selector}")
                element = page.query_selector(selector)
                if element is None:
                    log_error(f"Error: No element matches selector '{selector}'")
                    browser.close()
                    sys.exit(1)
                element.scroll_into_view_if_needed()
                screenshot_bytes = element.screenshot(type=fmt if fmt != "jpg" else "jpeg")
            else:
                screenshot_bytes = page.screenshot(type=fmt if fmt != "jpg" else "jpeg", full_page=False)

            browser.close()

    except Exception as e:
        error_msg = str(e)
        if "Timeout" in error_msg or "timeout" in error_msg:
            log_error(f"Error: Page load timed out (30s limit): {url}")
        else:
            log_error(f"Error: {error_msg}")
        sys.exit(1)

    # Determine output path
    if output_path is None:
        output_path = f"screenshot.{fmt}"

    dest = resolve_output_path(output_path, fmt, force)
    save_image_bytes(screenshot_bytes, dest, None)  # Already in correct format

    elapsed = time.time() - start
    log_verbose(verbose, quiet, f"Saved: {dest} ({elapsed:.1f}s)")

    if to_clipboard:
        success = copy_to_clipboard(screenshot_bytes)
        if success:
            log_verbose(verbose, quiet, "Copied to clipboard.")
        else:
            log_error("Error: Failed to copy to clipboard.")
            if not dest.exists():
                sys.exit(1)

    if not quiet:
        click.echo(f"✓ {dest}")
