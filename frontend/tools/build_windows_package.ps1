param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$ToolDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Resolve-Path (Join-Path $ToolDir "..")
$ProjectRoot = Resolve-Path (Join-Path $FrontendDir "..")
$SpecPath = Join-Path $ProjectRoot "build\windows\RHYME.spec"
$DistPath = Join-Path $ProjectRoot "dist\windows"
$WorkPath = Join-Path $ProjectRoot "build\pyinstaller"

Set-Location $ProjectRoot

if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    throw "Missing .venv. Please create a virtual environment at project root first."
}

. .\.venv\Scripts\Activate.ps1

python -m pip install -U pyinstaller

if ($Clean) {
    if (Test-Path $DistPath) {
        Remove-Item $DistPath -Recurse -Force
    }
    if (Test-Path $WorkPath) {
        Remove-Item $WorkPath -Recurse -Force
    }
}

python -m PyInstaller --noconfirm --clean --distpath $DistPath --workpath $WorkPath $SpecPath
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Write-Host "Build finished: ${DistPath}\RHYME\RHYME.exe"

