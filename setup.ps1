# Setup and Test Script for Windows PowerShell
# Run this script to set up and test the Kafka Order Processing System

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Kafka Order Processing System - Setup" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

# Step 1: Check Docker
Write-Host "[1/5] Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found or not running!" -ForegroundColor Red
    Write-Host "   Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Step 2: Check Python
Write-Host "`n[2/5] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found!" -ForegroundColor Red
    Write-Host "   Please install Python 3.8 or later." -ForegroundColor Red
    exit 1
}

# Step 3: Install Python Dependencies
Write-Host "`n[3/5] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Step 4: Start Docker Containers
Write-Host "`n[4/5] Starting Kafka infrastructure..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Kafka services started successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to start Kafka services" -ForegroundColor Red
    Write-Host "   Make sure Docker Desktop is running" -ForegroundColor Red
    exit 1
}

# Step 5: Wait for services to initialize
Write-Host "`n[5/5] Waiting for services to initialize..." -ForegroundColor Yellow
Write-Host "   This may take 30-60 seconds..." -ForegroundColor Gray

for ($i = 60; $i -gt 0; $i--) {
    Write-Progress -Activity "Initializing Kafka services" -Status "Time remaining: $i seconds" -PercentComplete ((60-$i)/60*100)
    Start-Sleep -Seconds 1
}
Write-Progress -Activity "Initializing Kafka services" -Completed

# Verify services
Write-Host "`n✓ Checking service status..." -ForegroundColor Yellow
docker-compose ps

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete! ✓" -ForegroundColor Green
Write-Host "================================================`n" -ForegroundColor Cyan

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Open a new terminal and run: " -NoNewline
Write-Host "python consumer.py" -ForegroundColor Cyan
Write-Host "2. Open another terminal and run: " -NoNewline
Write-Host "python producer.py" -ForegroundColor Cyan
Write-Host "`nOr run the automated test: " -NoNewline
Write-Host ".\test-system.ps1`n" -ForegroundColor Cyan
