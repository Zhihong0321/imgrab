# Requirements Document

## Introduction

Image Grabber CLI is a Python command-line tool that downloads and saves images from the internet to the local filesystem. The tool addresses the frustration of needing web images during development but lacking a reliable, no-excuses way to grab them programmatically. It supports multiple acquisition methods — direct HTTP download, headless browser rendering with screenshot capture, and clipboard copy — ensuring that any image a browser can display can be saved locally on Windows.

**Recommended Stack:**
- **Language:** Python 3.10+
- **HTTP Downloads:** `httpx` (async, HTTP/2 support, follows redirects)
- **Browser Automation:** `playwright` (headless Chromium for rendering JS-heavy pages, capturing screenshots of dynamic/canvas images)
- **CLI Framework:** `click` (clean argument parsing, subcommands, help generation)
- **Image Processing:** `Pillow` (format conversion, validation, clipboard integration on Windows)
- **Clipboard:** `win32clipboard` via `pywin32` (Windows clipboard image copy)
- **Packaging:** `pyproject.toml` with entry point for `imgrab` CLI command

## Glossary

- **CLI**: Command-Line Interface — the terminal-based user interface for the tool
- **Image_Grabber**: The main application system that orchestrates image acquisition
- **Downloader**: The component responsible for direct HTTP/HTTPS image downloads
- **Browser_Engine**: The headless browser component (Playwright/Chromium) used to render pages and capture screenshots
- **Clipboard_Manager**: The component that copies image data to the Windows clipboard
- **URL**: Uniform Resource Locator — the web address of the target image or page
- **CSS_Selector**: A CSS selector string used to identify a specific image element on a page
- **Output_Path**: The local filesystem path where the saved image is written
- **User_Agent**: The HTTP User-Agent header string sent with requests to mimic a real browser

## Requirements

### Requirement 1: Direct Image Download

**User Story:** As a developer, I want to download an image directly from a URL, so that I can save it to my local machine without needing a browser.

#### Acceptance Criteria

1. WHEN a valid image URL is provided, THE Downloader SHALL download the image over HTTP or HTTPS and save it to the specified Output_Path within 30 seconds of initiating the connection
2. WHEN no Output_Path is specified, THE Downloader SHALL save the image to the current working directory using the last path segment of the URL (excluding query parameters) as the filename, or "image" with the appropriate extension if no usable filename can be derived
3. IF the URL returns a Content-Type header that does not start with "image/", THEN THE Image_Grabber SHALL display an error message indicating the URL does not point to an image and exit with a non-zero status code
4. THE Downloader SHALL send a User_Agent header matching a current major-version Chrome browser string with each request
5. WHEN the server returns an HTTP redirect, THE Downloader SHALL follow up to 10 redirects to reach the final image
6. THE Image_Grabber SHALL accept custom headers specified as key-value pairs via a repeatable command-line option
7. IF the download fails due to a network error or connection timeout, THEN THE Image_Grabber SHALL display the error reason and exit with a non-zero status code
8. IF the download fails due to an HTTP 403 or 429 status, THEN THE Image_Grabber SHALL display the error and suggest using the screenshot method as a fallback
9. IF the server returns an HTTP error status other than 403 or 429, THEN THE Image_Grabber SHALL display an error message including the HTTP status code and exit with a non-zero status code
10. IF the redirect limit of 10 is exceeded, THEN THE Image_Grabber SHALL display an error message indicating too many redirects and exit with a non-zero status code
11. IF writing the image file to disk fails, THEN THE Image_Grabber SHALL display an error message indicating the write failure reason and exit with a non-zero status code

### Requirement 2: Browser Screenshot Capture

**User Story:** As a developer, I want to capture a screenshot of an image rendered in a headless browser, so that I can save images that require JavaScript rendering, authentication cookies, or are otherwise not directly downloadable.

#### Acceptance Criteria

1. WHEN a URL and the screenshot mode flag are provided, THE Browser_Engine SHALL load the page in a headless Chromium browser and capture a screenshot
2. WHEN a CSS_Selector is provided with screenshot mode, THE Browser_Engine SHALL capture only the first element matching that selector
3. WHEN no CSS_Selector is provided with screenshot mode, THE Browser_Engine SHALL capture the full visible viewport at a default resolution of 1280x720 pixels
4. WHILE the page is loading, THE Browser_Engine SHALL wait until network activity is idle for 2 seconds before capturing, up to a maximum total page load timeout of 30 seconds
5. WHEN the page requires scrolling to reveal the target element, THE Browser_Engine SHALL scroll the element into view before capturing
6. THE Browser_Engine SHALL save the screenshot in PNG format by default
7. WHEN a JPEG or WebP output format is specified, THE Browser_Engine SHALL convert the screenshot to the requested format
8. IF the CSS_Selector matches no elements, THEN THE Image_Grabber SHALL display an error message listing the selector that failed and exit with a non-zero status code
9. IF the page fails to load due to a navigation error or the 30-second timeout is exceeded, THEN THE Image_Grabber SHALL display an error message indicating the failure reason and exit with a non-zero status code

### Requirement 3: Clipboard Copy

**User Story:** As a developer, I want to copy a downloaded image to the Windows clipboard, so that I can paste it directly into design tools or documents without navigating the filesystem.

#### Acceptance Criteria

1. WHEN the clipboard flag is provided along with a URL, THE Clipboard_Manager SHALL download the image and copy it to the Windows clipboard as a bitmap
2. WHEN the clipboard flag is combined with screenshot mode, THE Clipboard_Manager SHALL copy the captured screenshot to the Windows clipboard as a bitmap
3. WHEN the clipboard flag is provided alongside an Output_Path, THE Image_Grabber SHALL both save the file to the Output_Path and copy the image to the clipboard
4. WHEN the clipboard flag is provided without an Output_Path, THE Image_Grabber SHALL copy the image to the clipboard without saving a file to disk
5. IF copying to the clipboard fails and an Output_Path was specified, THEN THE Image_Grabber SHALL save the file to disk, display an error message indicating the clipboard failure, and exit with a non-zero status code
6. IF copying to the clipboard fails and no Output_Path was specified, THEN THE Image_Grabber SHALL display an error message indicating the clipboard failure and exit with a non-zero status code
7. WHEN the image is successfully copied to the clipboard, THE Image_Grabber SHALL display a confirmation message indicating the clipboard copy succeeded
8. IF the source image is an animated format, THEN THE Clipboard_Manager SHALL copy only the first frame to the clipboard as a bitmap

### Requirement 4: Batch Download

**User Story:** As a developer, I want to download multiple images at once from a list of URLs, so that I can efficiently gather all assets needed for a project.

#### Acceptance Criteria

1. WHEN a text file containing one URL per line is provided, THE Image_Grabber SHALL download each image and save it to the specified output directory using the filename derived from each URL
2. WHILE batch mode is active, THE Image_Grabber SHALL process downloads concurrently with a default concurrency of 4 and a maximum configurable concurrency of 16
3. IF a URL in the batch fails due to a network error, HTTP error, or non-image content type, THEN THE Image_Grabber SHALL output the failed URL and the failure reason to standard error and continue processing remaining URLs
4. WHEN batch mode completes, THE Image_Grabber SHALL display a summary to standard output showing the count of successful downloads, the count of failures, and total time elapsed in seconds
5. THE Image_Grabber SHALL skip blank lines and lines starting with "#" in the batch file
6. IF the specified batch file does not exist or cannot be read, THEN THE Image_Grabber SHALL display an error message indicating the file path that failed and exit with a non-zero status code
7. IF a line in the batch file contains a malformed URL, THEN THE Image_Grabber SHALL treat it as a failure, include it in the failure count, and continue processing remaining URLs
8. WHEN no output directory is specified in batch mode, THE Image_Grabber SHALL save all images to the current working directory

### Requirement 5: Page Image Extraction

**User Story:** As a developer, I want to extract all image URLs from a web page, so that I can discover and download images without manually inspecting page source.

#### Acceptance Criteria

1. WHEN a page URL and the extract mode flag are provided, THE Browser_Engine SHALL load the page, wait until network activity is idle for 2 seconds, and extract all unique image source URLs
2. THE Browser_Engine SHALL extract URLs from img src attributes, CSS background-image properties, and srcset attributes, resolving any relative URLs to absolute URLs using the page's base URL
3. WHEN the extract mode is combined with a download flag, THE Image_Grabber SHALL download all extracted images concurrently (default concurrency of 4) to the specified output directory
4. WHEN extract mode is used without a download flag, THE Image_Grabber SHALL print the list of discovered image URLs to standard output, one URL per line
5. WHEN a CSS_Selector filter is provided in extract mode, THE Browser_Engine SHALL extract images only from elements matching that selector
6. IF the page fails to load or returns a non-success HTTP status, THEN THE Image_Grabber SHALL display an error message indicating the failure reason and exit with a non-zero status code
7. IF a CSS_Selector filter is provided and matches no elements, THEN THE Image_Grabber SHALL display an error message listing the selector that failed

### Requirement 6: Output Format and Naming

**User Story:** As a developer, I want control over the output filename and image format, so that I can organize downloaded images to fit my project structure.

#### Acceptance Criteria

1. WHEN an output format flag is provided, THE Image_Grabber SHALL convert the downloaded image to the specified format (PNG, JPEG, WebP, GIF)
2. WHEN the output filename has no extension and a format flag is provided, THE Image_Grabber SHALL append the extension corresponding to the specified format (.png, .jpg, .webp, .gif); WHEN no format flag is provided, THE Image_Grabber SHALL append the extension matching the source image format
3. WHEN saving to a directory that does not exist, THE Image_Grabber SHALL create the directory structure up to 10 levels deep before saving
4. WHEN a file already exists at the Output_Path and no force flag is provided, THE Image_Grabber SHALL append a numeric suffix in the format `_1`, `_2`, up to `_99` to the filename before the extension to produce a unique path
5. WHEN the force flag is provided, THE Image_Grabber SHALL overwrite existing files without prompting
6. IF format conversion fails, THEN THE Image_Grabber SHALL display an error message indicating the source format, the target format, and the reason for failure, and exit with a non-zero status code
7. IF writing the file to disk fails due to permission errors or insufficient disk space, THEN THE Image_Grabber SHALL display an error message indicating the failure reason and exit with a non-zero status code

### Requirement 7: CLI Interface and Help

**User Story:** As a developer, I want a clear and intuitive command-line interface, so that I can use the tool efficiently without memorizing complex syntax.

#### Acceptance Criteria

1. THE CLI SHALL provide a --help flag and a -h shorthand on the root command and each subcommand that displays usage syntax, available options, and at least one usage example per subcommand
2. THE CLI SHALL support the following subcommands: download, screenshot, extract, batch
3. WHEN an invalid command or missing required argument is provided, THE CLI SHALL display an error message identifying the invalid input, followed by the correct usage syntax for the intended command
4. WHEN the --verbose flag is provided, THE CLI SHALL output progress information including the current operation name, the target URL or file path being processed, and elapsed time for each step
5. WHEN the --quiet flag is provided, THE CLI SHALL suppress all output to stdout and stderr except error messages indicating operation failure
6. IF both --verbose and --quiet flags are provided, THEN THE CLI SHALL display an error message indicating the flags are mutually exclusive and exit with a non-zero status code
7. THE CLI SHALL exit with status code 0 on success and exit code 1 on failure
8. THE CLI SHALL provide a --version flag that displays the tool name and current version number
