# imgrab

No-excuses image grabber CLI. Download, screenshot, or clipboard-copy any image from the web.

## One-Step Install

```bash
pip install git+https://github.com/Zhihong0321/imgrab.git && playwright install chromium
```

Or on Windows PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

That's it. Now use `imgrab` (or `py -m imgrab` if not on PATH).

## Quick Start

```bash
# Direct download
imgrab download https://example.com/photo.jpg -o ./assets/photo.jpg

# Screenshot (for JS-rendered, auth-gated, or blocked images)
imgrab screenshot https://example.com/page --selector "img.hero" -o hero.png

# Extract all images from a page
imgrab extract https://example.com/gallery --download -o ./images/

# Batch download from a URL list
imgrab batch urls.txt -o ./assets/

# Copy to Windows clipboard (paste into Figma, docs, etc.)
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
| `--format png|jpg|webp|gif` | Convert output format |
| `--selector "css"` | Target specific element |
| `--clipboard` | Copy to Windows clipboard |
| `--header "Key: Value"` | Custom HTTP header (repeatable) |
| `--force` | Overwrite existing files |
| `-v` / `-q` | Verbose / quiet mode (on root command) |

## For AI Coding Agents

This repo includes a Kiro steering file that teaches AI agents to use imgrab automatically.

### Setup for any project (one line):

```bash
mkdir -p .kiro/steering && curl -sL https://raw.githubusercontent.com/Zhihong0321/imgrab/main/.kiro/steering/imgrab.md -o .kiro/steering/imgrab.md
```

Or on Windows:
```powershell
New-Item -ItemType Directory -Force -Path .kiro\steering | Out-Null; Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Zhihong0321/imgrab/main/.kiro/steering/imgrab.md" -OutFile ".kiro\steering\imgrab.md"
```

Now any AI agent (Kiro, Cursor, etc.) working in that project will use `imgrab` for image tasks instead of refusing.

## Stack

- Python 3.10+
- httpx (async HTTP/2 downloads)
- playwright (headless Chromium for screenshots)
- click (CLI framework)
- Pillow (image processing/conversion)
- pywin32 (Windows clipboard)

## License

MIT
