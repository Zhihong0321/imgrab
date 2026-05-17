# Requirements Document

## Introduction

This feature adds a `search` command to the imgrab CLI that uses Gemini CLI (Google's AI command-line tool) to perform web image searches based on a text query. The command accepts a natural language query, invokes Gemini CLI to find relevant image URLs on the web, presents the results to the user, and then downloads the images using the existing imgrab download infrastructure.

## Glossary

- **Imgrab**: The existing image grabber CLI tool that provides download, screenshot, extract, and batch commands.
- **Search_Command**: The new `imgrab search` subcommand that orchestrates query-to-download workflow.
- **Gemini_CLI**: Google's Gemini command-line interface tool (`gemini`) used as an external process to perform AI-powered web image searches.
- **Query**: A natural language text string describing the desired images (e.g., "cat playing piano").
- **Image_URL_List**: A list of image URLs returned by Gemini CLI as search results.
- **Downloader**: The existing imgrab download infrastructure (single and batch) that fetches images from URLs.

## Requirements

### Requirement 1: Execute Image Search via Gemini CLI

**User Story:** As a user, I want to search for images using a text query, so that I can find and download images without manually browsing the web.

#### Acceptance Criteria

1. WHEN a non-empty query string is provided, THE Search_Command SHALL invoke Gemini_CLI as a subprocess with a prompt instructing it to find image URLs matching the query, with a subprocess timeout of 60 seconds.
2. THE Search_Command SHALL pass the query to Gemini_CLI in a prompt that requests URLs ending in a common image extension (.jpg, .jpeg, .png, .gif, .webp) or URLs with an image Content-Type, suitable for direct HTTP download.
3. WHEN Gemini_CLI returns output, THE Search_Command SHALL parse the output to extract URLs that match the pattern of an absolute HTTP or HTTPS URL containing a path segment with a recognized image extension (.jpg, .jpeg, .png, .gif, .webp) or a recognized image hosting domain.
4. THE Search_Command SHALL accept an optional `--limit` parameter to specify the maximum number of image URLs to retrieve, accepting values from 1 to 50, defaulting to 5.
5. WHEN Gemini_CLI returns fewer URLs than the requested limit, THE Search_Command SHALL proceed with the available URLs without error.
6. IF the Gemini_CLI subprocess is not found on the system PATH or fails to start, THEN THE Search_Command SHALL display an error message indicating that Gemini CLI is not available and exit with a non-zero status code.
7. IF the Gemini_CLI subprocess exceeds the 60-second timeout or returns a non-zero exit code, THEN THE Search_Command SHALL display an error message indicating the failure reason and exit with a non-zero status code.
8. IF Gemini_CLI returns output containing zero extractable image URLs, THEN THE Search_Command SHALL display a message indicating no images were found for the query and exit with a non-zero status code.

### Requirement 2: Validate Gemini CLI Availability

**User Story:** As a user, I want clear feedback when Gemini CLI is not installed, so that I know what to set up before using the search feature.

#### Acceptance Criteria

1. WHEN the search command is invoked, THE Search_Command SHALL verify that the `gemini` executable is available on the system PATH before proceeding with the search operation.
2. IF Gemini_CLI is not found on the system PATH, THEN THE Search_Command SHALL display an error message indicating that Gemini CLI must be installed and provide a reference to the installation instructions, and exit with a non-zero status code.
3. IF Gemini_CLI execution fails with a non-zero exit code, THEN THE Search_Command SHALL display the stderr output from Gemini_CLI and exit with a non-zero status code.
4. IF Gemini_CLI execution exceeds a 60-second timeout, THEN THE Search_Command SHALL terminate the Gemini_CLI process, display an error message indicating the operation timed out, and exit with a non-zero status code.

### Requirement 3: Parse and Validate Image URLs

**User Story:** As a user, I want only valid image URLs to be processed, so that downloads do not fail on malformed or non-image links.

#### Acceptance Criteria

1. WHEN Gemini_CLI output is received, THE Search_Command SHALL extract all strings matching HTTP or HTTPS URL patterns (scheme followed by "://" followed by a valid host and path) from the output.
2. THE Search_Command SHALL filter extracted URLs to retain only those whose URL path component (excluding query parameters and fragments) ends with a case-insensitive image file extension (jpg, jpeg, png, gif, webp, svg, bmp, tiff) or whose host matches a known image-hosting domain (e.g., i.imgur.com, images.unsplash.com, pbs.twimg.com).
3. IF no valid image URLs are found in the Gemini_CLI output, THEN THE Search_Command SHALL display a message indicating no images were found for the query and exit with a zero status.
4. THE Search_Command SHALL deduplicate extracted URLs using exact string comparison so that each unique URL appears only once in the Image_URL_List.
5. IF the number of valid image URLs extracted exceeds 50, THEN THE Search_Command SHALL retain only the first 50 URLs in the order they appeared in the Gemini_CLI output.

### Requirement 4: Display Search Results

**User Story:** As a user, I want to see the list of found image URLs before downloading, so that I can review what will be downloaded.

#### Acceptance Criteria

1. WHEN valid image URLs are extracted, THE Search_Command SHALL display the list of image URLs to standard output, each prefixed with its sequential number starting at 1 in the format `<number>. <URL>`, one entry per line.
2. THE Search_Command SHALL accept a `--no-download` flag that displays the numbered URL list without proceeding to download.
3. WHILE the `--no-download` flag is not set and the `--yes` flag is not provided, THE Search_Command SHALL prompt the user for confirmation before proceeding to download, accepting "y" or "yes" (case-insensitive) to proceed and any other input to abort.
4. WHEN the `--yes` flag is provided and the `--no-download` flag is not set, THE Search_Command SHALL skip the confirmation prompt and proceed directly to download.
5. IF both the `--yes` flag and the `--no-download` flag are provided, THEN THE Search_Command SHALL display the URL list without downloading and ignore the `--yes` flag.

### Requirement 5: Download Search Results

**User Story:** As a user, I want found images to be downloaded automatically, so that I get the images on disk without additional manual steps.

#### Acceptance Criteria

1. WHEN the user confirms download via an interactive yes/no prompt or the `--yes` flag is set, THE Search_Command SHALL download all images in the Image_URL_List using the existing Downloader infrastructure.
2. IF the user declines the interactive download prompt, THEN THE Search_Command SHALL skip downloading and exit with status code 0.
3. THE Search_Command SHALL accept an optional `-o`/`--output` parameter to specify the output directory for downloaded images, defaulting to the current working directory.
4. THE Search_Command SHALL accept an optional `--format` parameter to convert downloaded images to a specified format (png, jpg, webp, gif).
5. THE Search_Command SHALL accept an optional `--concurrency` parameter to control parallel downloads, accepting a value between 1 and 16 inclusive, defaulting to 4.
6. WHEN a download fails for a specific URL, THE Search_Command SHALL output the failed URL and the failure reason to standard error and continue downloading remaining URLs.
7. WHEN all downloads complete, THE Search_Command SHALL display a summary to standard output showing the count of successful downloads, the count of failed downloads, and total elapsed time in seconds.
8. IF the Image_URL_List is empty, THEN THE Search_Command SHALL display a message indicating no images were found and exit with status code 0 without prompting for download.

### Requirement 6: Integration with Existing CLI Structure

**User Story:** As a developer, I want the search command to follow existing imgrab conventions, so that the codebase remains consistent and maintainable.

#### Acceptance Criteria

1. THE Search_Command SHALL be registered as a click subcommand named `search` under the main imgrab CLI group.
2. WHEN the `--verbose` flag is active, THE Search_Command SHALL output progress information including the current operation name, the target query or URL being processed, and elapsed time for each step; WHEN the `--quiet` flag is active, THE Search_Command SHALL suppress all output to stdout except error messages indicating operation failure.
3. THE Search_Command SHALL accept the query as a required positional argument of 1 to 500 characters (e.g., `imgrab search "cat playing piano"`).
4. WHEN the `--clipboard` flag is provided, THE Search_Command SHALL copy the first downloaded image to the Windows clipboard as a bitmap.
5. IF copying to the clipboard fails and an output file was saved, THEN THE Search_Command SHALL display an error message indicating the clipboard failure and exit with a non-zero status code while preserving the saved file.
6. IF copying to the clipboard fails and no output file was saved, THEN THE Search_Command SHALL display an error message indicating the clipboard failure and exit with a non-zero status code.
7. THE Search_Command SHALL use the shared User_Agent string, a connection timeout of 30 seconds, and a maximum of 10 redirects, matching the HTTP client configuration used by the download command.

### Requirement 7: Gemini CLI Prompt Engineering

**User Story:** As a developer, I want the prompt sent to Gemini CLI to be well-structured, so that search results are reliable and contain usable direct image URLs.

#### Acceptance Criteria

1. THE Search_Command SHALL construct a prompt for Gemini_CLI that includes the user's Query and explicitly instructs Gemini_CLI to return only direct image file URLs ending in common image extensions (jpg, jpeg, png, gif, webp, svg, bmp, tiff) rather than web page URLs that contain or display images.
2. THE Search_Command SHALL include the requested limit number in the prompt to Gemini_CLI so that Gemini_CLI is instructed to return no more than that number of URLs.
3. THE Search_Command SHALL instruct Gemini_CLI to return URLs as plain text with one URL per line, without markdown formatting, numbering, or surrounding text.
4. THE Search_Command SHALL set a configurable timeout for Gemini_CLI execution via a `--timeout` parameter accepting a value between 10 and 300 seconds, defaulting to 60 seconds.
5. THE Search_Command SHALL instruct Gemini_CLI within the prompt to exclude URLs from image-aggregator pages (such as search engine result pages or social media galleries) and return only URLs that point directly to an image file.

### Requirement 8: Search Command Timeout and Process Management

**User Story:** As a user, I want the search command to handle slow or hanging Gemini CLI processes gracefully, so that my terminal does not become unresponsive.

#### Acceptance Criteria

1. THE Search_Command SHALL accept an optional `--timeout` parameter accepting a value between 10 and 300 seconds to override the default 60-second Gemini_CLI execution timeout.
2. WHEN the timeout is reached, THE Search_Command SHALL terminate the Gemini_CLI subprocess, display an error message indicating the operation timed out after the specified number of seconds, and exit with status code 1.
3. WHEN the user sends a keyboard interrupt (Ctrl+C) during Gemini_CLI execution, THE Search_Command SHALL terminate the Gemini_CLI subprocess within 2 seconds, display no output, and exit with status code 130.
