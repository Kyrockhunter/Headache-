
Write-Host "`n=== Fantasy v4: setup & run ===`n"
if (-not (Test-Path .\.venv)) { Write-Host "Creating .venv..."; python -m venv .venv }
& .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install pandas numpy pulp pytest pyyaml
python .\main.py --objective cash --risk 0.1 --iterations 10000
