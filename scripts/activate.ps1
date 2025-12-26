# Activate AI-Defender virtual environment
# Run: .\scripts\activate.ps1

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"

if (Test-Path $VenvPath) {
    Write-Host "Activating AI-Defender virtual environment..." -ForegroundColor Cyan
    & $VenvPath

    Write-Host @"

AI-Defender Environment Active
==============================
Python: $(python --version)
Project: $ProjectRoot

Quick Commands:
  python src/memory/short_term.py    # Test short-term memory
  python src/memory/long_term.py     # Test long-term memory (needs Qdrant)
  streamlit run src/dashboard/app.py # Launch dashboard
  pytest                             # Run tests

Start Qdrant (for long-term memory):
  docker run -p 6333:6333 -v ${ProjectRoot}\data\qdrant:/qdrant/storage qdrant/qdrant

"@ -ForegroundColor Green
} else {
    Write-Host "Error: Virtual environment not found at $VenvPath" -ForegroundColor Red
    Write-Host "Run 'python -m venv venv' first" -ForegroundColor Yellow
}
