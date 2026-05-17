"""CLI entry point for imgrab."""

import click

from imgrab import __version__
from imgrab.download import download_cmd
from imgrab.screenshot import screenshot_cmd
from imgrab.extract import extract_cmd
from imgrab.batch import batch_cmd


@click.group()
@click.version_option(version=__version__, prog_name="imgrab")
@click.option("--verbose", "-v", is_flag=True, help="Enable detailed progress output.")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output except errors.")
@click.pass_context
def cli(ctx, verbose, quiet):
    """imgrab - No-excuses image grabber. Download, screenshot, or clipboard-copy any image."""
    if verbose and quiet:
        raise click.UsageError("--verbose and --quiet are mutually exclusive.")
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


cli.add_command(download_cmd, "download")
cli.add_command(screenshot_cmd, "screenshot")
cli.add_command(extract_cmd, "extract")
cli.add_command(batch_cmd, "batch")


if __name__ == "__main__":
    cli()
