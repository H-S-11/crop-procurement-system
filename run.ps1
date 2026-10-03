# run.ps1
Write-Host "Starting Crop Procurement System..."
$ErrorActionPreference = "Stop"

# Start backend in a background job
Write-Host "Starting Backend API..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\python.exe main.py"

# Start frontend
Write-Host "Starting Frontend Dashboard..."
cd frontend
npm run dev
