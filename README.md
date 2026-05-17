# imgrab

No-excuses image grabber CLI. Download, screenshot, or clipboard-copy any image from the web.

## Install

```bash
pip install -e .
playwright install chromium
```

## Quick Start

```bash
# Direct download
imgrab download https://example.com/photo.jpg -o ./assets/photo.jpg

# Screenshot (for JS-rendered or blocked images)
imgrab screenshot https://example.com/page --selector "img.hero" -o hero.png

# Extract all images from a page
imgrab extract https://example.com/gallery --download -o ./images/

# Batch download from a URL list
imgrab batch urls.txt -o ./assets/

# Copy to clipboard
imgrab download https://example.com/icon.png --clipboard
```

## Commands

| Command | Purpose |
|---------|---------|
| `download` | Direct HTTP download of an image URL |
| `screenshot` | Headless browser screenshot (handles JS, auth, canvas) |
| `extract` | Find and list/download all images on a page |
| `batch` | Download multiple images from a text file of URLs |

## Key Flags

| Flag | Purpose |
|------|---------|
| `-o, --output` | Output file or directory |
| `--format png\|jpg\|webp\|gif` | Convert output format |
| `--selector "css"` | Target specific element |
| `--clipboard` | Copy to Windows clipboard |
| `--header "Key: Value"` | Custom HTTP header (repeatable) |
| `--force` | Overwrite existing files |
| `--verbose` / `--quiet` | Control output verbosity |

## For AI Agents

This repo includes a Kiro steering file at `.kiro/steering/imgrab.md` that instructs AI coding agents how to use this tool. Copy the `.kiro/` directory into any project where you want your AI agent to automatically use imgrab for image tasks.

### Quick setup for any project:

```bash
# Install imgrab globally
pip install git+https://github.com/xuahipn/imgrab.git

# Copy the steering file to your project
cp -r path/to/imgrab/.kiro/steering/imgrab.md your-project/.kiro/steering/imgrab.md
```

Now any AI agent working in that project will know to use `imgrab` instead of refusing image downloads.

## Stack

- Python 3.10+
- httpx (async HTTP/2 downloads)
- playwright (headless Chromium)
- click (CLI framework)
- Pillow (image processing)
- pywin32 (Windows clipboard)

## License

MIT
