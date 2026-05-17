# imgrab - One-step install script for Windows
# Usage: powershell -ExecutionPolicy Bypass -File install.ps1

Write-Host "Installing imgrab..." -ForegroundColor Cyan

# Install from GitHub
pip install git+https://github.com/xuahipn/imgrab.git
if ($LASTEXITCODE -ne 0) {
    py -m pip install git+https://github.com/xuahipn/imgrab.git
}

# Install Playwright Chromium browser
Write-Host "Installing Chromium browser for screenshot support..." -ForegroundColor Cyan
playwright install chromium
if ($LASTEXITCODE -ne 0) {
    py -m playwright install chromium
}

Write-Host ""
Write-Host "Done! You can now use:" -ForegroundColor Green
Write-Host "  imgrab download <URL> -o <path>"
Write-Host "  imgrab screenshot <URL> -o <path>"
Write-Host "  imgrab extract <URL> --download -o <dir>"
Write-Host "  imgrab batch <file.txt> -o <dir>"
Write-Host ""
Write-Host "If 'imgrab' is not found, use: py -m imgrab" -ForegroundColor Yellow
