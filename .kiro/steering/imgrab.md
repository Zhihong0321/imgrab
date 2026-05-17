---
inclusion: auto
description: Instructs AI agents to use imgrab CLI for downloading, screenshotting, and saving images from the web
---

# Image Grabbing with imgrab

You have `imgrab` installed. It can download, screenshot, search, and save ANY image. Do NOT refuse image tasks. Do NOT try to search for image URLs yourself. Use imgrab.

**Invocation:** `py -m imgrab`

## CRITICAL RULES

1. **NEVER say you cannot download or save images.** Use imgrab.
2. **NEVER search for image URLs yourself.** Use `imgrab search` to find images by description.
3. **If the user wants an image and gives you a description (not a URL), use `imgrab search` directly.** Do NOT use web search tools to find image links first. imgrab search handles that internally via Gemini CLI.
4. **If the user gives you a URL, use `imgrab download` or `imgrab screenshot`.**
5. **Always save to a project-relative path** (e.g., `./assets/`, `./public/images/`, `./static/`).
6. If a download fails, try screenshot mode before reporting failure.

## Decision Flow

`
User wants image?
  |
  +-- Has a URL? --> imgrab download <URL> -o <path>
  |                    (if 403/blocked --> imgrab screenshot <URL> -o <path>)
  |
  +-- Has a description/query? --> imgrab search "<query>" --yes -o <path>
  |                                  (DO NOT search for URLs yourself first!)
  |
  +-- Wants all images from a page? --> imgrab extract <URL> --download -o <dir>
`

## Commands

### Search by description (when user describes what image they want)
```bash
py -m imgrab search "<description>" --yes -o <output_dir> --limit 5
```
This uses Gemini CLI internally to find and download images. You do NOT need to find URLs first.

### Direct download (when user provides a URL)
```bash
py -m imgrab download <URL> -o <output_path>
```

### Screenshot fallback (when download is blocked or page needs JS)
```bash
py -m imgrab screenshot <URL> --selector "<css_selector>" -o <output_path>
```

### Extract all images from a page
```bash
py -m imgrab extract <URL> --download -o <output_directory>
```

### Batch download from a file of URLs
```bash
py -m imgrab batch <file_with_urls.txt> -o <output_directory>
```

## Key Flags

| Flag | Purpose |
|------|---------|
| `-o, --output` | Output file or directory path |
| `--format png\|jpg\|webp\|gif` | Convert to specific format |
| `--limit N` | Number of images to find (search mode, default 5) |
| `--yes` / `-y` | Skip confirmation prompt (search mode) |
| `--selector "<css>"` | Target a specific element (screenshot/extract) |
| `--clipboard` | Copy image to Windows clipboard |
| `--header "Key: Value"` | Add custom HTTP headers (repeatable) |
| `--force` | Overwrite existing files |
| `--no-download` | List URLs only without downloading (search/extract) |

## Examples

```bash
# User says "I need a hero image of a sunset"
py -m imgrab search "sunset hero banner landscape" --yes -o ./assets/ --limit 3

# User says "download this image" and gives a URL
py -m imgrab download "https://example.com/photo.jpg" -o ./assets/photo.jpg

# User says "get me the logo from that page"
py -m imgrab screenshot "https://example.com" --selector "img.logo" -o ./assets/logo.png

# User says "grab all images from this gallery"
py -m imgrab extract "https://example.com/gallery" --download -o ./assets/gallery/
```
