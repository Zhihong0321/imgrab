"""Shared utilities."""

import sys
import click

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

IMAGE_CONTENT_TYPES = {
    "image/png", "image/jpeg", "image/gif", "image/webp",
    "image/svg+xml", "image/bmp", "image/tiff", "image/x-icon",
}


def log_verbose(verbose: bool, quiet: bool, message: str) -> None:
    """Print message only in verbose mode."""
    if verbose and not quiet:
        click.echo(f"  {message}", err=False)


def log_error(message: str) -> None:
    """Print error message to stderr."""
    click.echo(message, err=True)
