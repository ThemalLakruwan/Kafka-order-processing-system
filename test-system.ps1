# Test Script for Kafka Order Processing System
# This script runs an automated test of the system

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Kafka System - Automated Test" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

# Check if services are running
Write-Host "Checking Kafka services..." -ForegroundColor Yellow
$services = docker-compose ps --services --filter "status=running"
$runningCount = ($services | Measure-Object -Line).Lines

if ($runningCount -lt 3) {
    Write-Host "✗ Not all services are running!" -ForegroundColor Red
    Write-Host "  Please run .\setup.ps1 first" -ForegroundColor Red
    exit 1
}

Write-Host "✓ All services are running`n" -ForegroundColor Green

# Start consumer in background
Write-Host "[1/3] Starting consumer in background..." -ForegroundColor Yellow
$consumerJob = Start-Job -ScriptBlock {
    Set-Location "d:\Ruhuna FoE\Semester 08\BigData\Assignment\BigDataCode"
    python consumer.py
}
Write-Host "✓ Consumer started (Job ID: $($consumerJob.Id))`n" -ForegroundColor Green

# Wait for consumer to initialize
Write-Host "Waiting for consumer to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Run producer
Write-Host "[2/3] Running producer (will produce 20 orders)..." -ForegroundColor Yellow
Write-Host "This will take about 40 seconds...`n" -ForegroundColor Gray

# Modify producer temporarily to produce fewer messages for faster testing
$producerOutput = python producer.py 2>&1
Write-Host $producerOutput

# Wait a bit for consumer to process
Write-Host "`n[3/3] Waiting for consumer to process all messages..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Get consumer output
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  Consumer Output (Last 50 lines)" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

$consumerOutput = Receive-Job -Job $consumerJob
if ($consumerOutput) {
    $consumerOutput | Select-Object -Last 50 | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "No output from consumer yet. It may still be initializing." -ForegroundColor Yellow
}

# Stop consumer
Write-Host "`nStopping consumer..." -ForegroundColor Yellow
Stop-Job -Job $consumerJob
Remove-Job -Job $consumerJob
Write-Host "✓ Consumer stopped`n" -ForegroundColor Green

# Show statistics
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Test Summary" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

# Check topics
Write-Host "Topics created:" -ForegroundColor Yellow
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

Write-Host "`n✓ Test completed!" -ForegroundColor Green
Write-Host "`nTo view DLQ messages, run:" -ForegroundColor Yellow
Write-Host "docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic orders-dlq --from-beginning`n" -ForegroundColor Cyan
