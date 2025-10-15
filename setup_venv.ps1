<#
setup_venv.ps1
-------------------------------------------------------------
Auto-setup script for Fantasy Simulation Engine v4 environment
-------------------------------------------------------------
#>

Write-Host "`n=== Fantasy_v4 Environment Setup ===`n"

# Step 1: Confirm Python is available
try {
    $pyVersion = python --version 2>$null
    if (-not $pyVersion) {
        Write-Host "❌ Python not found. Install Python 3.x before continuing." -ForegroundColor Red
        exit 1
    } else {
        Write-Host "✅ Python detected: $pyVersion"
    }
} catch {
    Write-Host "❌ Python not found or not in PATH." -ForegroundColor Red
    exit 1
}

# Step 2: Create virtual environment if missing
$venvPath = ".\.venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "🧱 Creating virtual environment..."
    python -m venv .venv
    if (-not (Test-Path $venvPath)) {
        Write-Host "❌ Failed to create .venv folder." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Virtual environment already exists."
}

# Step 3: Ensure execution policy allows script activation
$currentPolicy = Get-ExecutionPolicy -Scope CurrentUser
if ($currentPolicy -ne "RemoteSigned") {
    Write-Host "🔐 Adjusting PowerShell execution policy to RemoteSigned..."
    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force
    Write-Host "✅ Execution policy set to RemoteSigned."
} else {
    Write-Host "✅ Execution policy already set correctly."
}

# Step 4: Activate environment
Write-Host "🚀 Activating virtual environment..."
& ".\.venv\Scripts\Activate.ps1"

# Step 5: Verify pip works
try {
    $pipVer = pip --version
    Write-Host "✅ Pip detected: $pipVer"
} catch {
    Write-Host "❌ Pip not found inside virtual environment." -ForegroundColor Red
    exit 1
}

# Step 6: Confirm environment paths
Write-Host "`nPython path:"
where python
Write-Host "`nPip path:"
where pip

# Step 7: Install core dependencies if missing
Write-Host "`n📦 Checking core dependencies..."
pip install --upgrade pip
pip install numpy pandas pyyaml reportlab pytest

Write-Host "`n✅ Environment setup complete!"
Write-Host "You are now inside the virtual environment (.venv)."
Write-Host "Next time, simply run:`n   .\\.venv\\Scripts\\Activate.ps1`n"
