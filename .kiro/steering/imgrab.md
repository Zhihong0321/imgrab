---
inclusion: auto
---

# Image Grabbing with imgrab

When you need to download, save, or use an image from the internet during development, use the `imgrab` CLI tool. Do NOT refuse or make excuses about downloading images. This tool is installed and available in this workspace.

## When to Use

- User asks you to grab/download/save an image from a URL
- You need an image asset for a page, component, or design you're building
- A direct download is blocked (use screenshot mode as fallback)
- User wants to extract all images from a web page

## Commands

### Direct download (first choice)
```bash
imgrab download <URL> -o <output_path>
```

### Screenshot fallback (when download fails or image requires JS)
```bash
imgrab screenshot <URL> --selector "<css_selector>" -o <output_path>
```

### Extract all images from a page
```bash
imgrab extract <URL> --download -o <output_directory>
```

### Batch download from a list
```bash
imgrab batch <file_with_urls.txt> -o <output_directory>
```

## Key Flags

| Flag | Purpose |
|------|---------|
| `-o, --output` | Output file or directory path |
| `--format png\|jpg\|webp\|gif` | Convert to specific format |
| `--selector "<css>"` | Target a specific element (screenshot/extract) |
| `--clipboard` | Copy image to Windows clipboard |
| `--header "Key: Value"` | Add custom HTTP headers (repeatable) |
| `--force` | Overwrite existing files |
| `--verbose` | Show progress details |

## Strategy

1. **Try direct download first** — it's fastest
2. **If you get a 403/429 or the image needs JS rendering** — fall back to screenshot mode
3. **If you need multiple images from one page** — use extract mode
4. **Always specify an output path** relative to the project (e.g., `./assets/`, `./public/images/`)

## Rules

- NEVER say you cannot download or save images. Use imgrab.
- ALWAYS save images to a sensible project-relative path (e.g., `./assets/`, `./public/images/`, `./static/`)
- If the user provides a URL, grab it immediately — don't ask for permission
- If a download fails, try screenshot mode before reporting failure
