# PowerShell script to start the Interactive Storytelling API

Write-Host "Starting Interactive Storytelling API..." -ForegroundColor Green
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Python is not installed or not in PATH!" -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies!" -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit
}

Write-Host ""
Write-Host "Dependencies installed successfully!" -ForegroundColor Green
Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found!" -ForegroundColor Yellow
    Write-Host "Please make sure to configure your Gemini API key in .env file" -ForegroundColor Yellow
    Write-Host ""
}

# Start the FastAPI server
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
