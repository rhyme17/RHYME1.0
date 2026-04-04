param(
    [switch]$Clean,
    [switch]$SkipInstall,
    [switch]$RegenerateSpec,
    [switch]$VerboseLog,
    [string]$LogPath = ""
)

$ErrorActionPreference = "Stop"

$script:LastCommand = ""

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARN", "ERROR")]
        [string]$Level = "INFO"
    )
    $time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$time] [$Level] $Message"
    Write-Host $line
    if ($script:EffectiveLogPath) {
        Add-Content -Path $script:EffectiveLogPath -Value $line
    }
}

function Invoke-CommandChecked {
    param(
        [string]$Label,
        [scriptblock]$Command
    )
    $script:LastCommand = $Label
    Write-Log "Start: $Label"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Failed: $Label (exit=$LASTEXITCODE)"
    }
    Write-Log "Done: $Label"
}

$ToolDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Resolve-Path (Join-Path $ToolDir "..")
$ProjectRoot = Resolve-Path (Join-Path $FrontendDir "..")
$SpecPath = Join-Path $ProjectRoot "build\windows\RHYME.spec"
$EntryScript = Join-Path $ProjectRoot "frontend\apps\desktop\windows\app.py"
$DistPath = Join-Path $ProjectRoot "dist"
$WorkPath = Join-Path $ProjectRoot "build\pyinstaller"
$LegacyDistPath = Join-Path $ProjectRoot "dist\windows"
$LegacyFlatDistPath = Join-Path $ProjectRoot "dist\RHYME"
$LegacyWorkPath = Join-Path $ProjectRoot "build\RHYME"
$IconSourcePath = Join-Path $ProjectRoot "img.png"
$IconOutputPath = Join-Path $ProjectRoot "build\windows\app.ico"
$IconGeneratorScript = Join-Path $ProjectRoot "frontend\tools\generate_windows_icon.py"

if ([string]::IsNullOrWhiteSpace($LogPath)) {
    $script:EffectiveLogPath = ""
} else {
    $logDir = Split-Path -Parent $LogPath
    if ($logDir -and -not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Force $logDir | Out-Null
    }
    $script:EffectiveLogPath = $LogPath
}

Set-Location $ProjectRoot

try {
    Write-Log "Project root: $ProjectRoot"
    if ($VerboseLog) {
        Write-Log "Params: Clean=$Clean SkipInstall=$SkipInstall RegenerateSpec=$RegenerateSpec"
        if ($script:EffectiveLogPath) {
            Write-Log "Log file: $script:EffectiveLogPath"
        }
    }

    if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
        throw "Missing .venv. Please create a virtual environment at project root first."
    }

    . .\.venv\Scripts\Activate.ps1
    Invoke-CommandChecked "python --version" { python --version }

    if (-not $SkipInstall) {
        Invoke-CommandChecked "pip install -U pyinstaller" { python -m pip install -U pyinstaller }
    } else {
        Write-Log "Skip dependency install (-SkipInstall)"
    }

    if (-not (Test-Path $EntryScript)) {
        throw "Entry script not found: $EntryScript"
    }

    if (Test-Path $IconSourcePath) {
        if (-not (Test-Path $IconGeneratorScript)) {
            throw "Icon generator script not found: $IconGeneratorScript"
        }
        Invoke-CommandChecked "Generate app icon" {
            python $IconGeneratorScript --source $IconSourcePath --output $IconOutputPath
        }
    } else {
        Write-Log "Icon source not found, skip icon generation: $IconSourcePath" "WARN"
    }

    if ($RegenerateSpec -and (Test-Path $SpecPath)) {
        Remove-Item $SpecPath -Force
        Write-Log "Deleted existing spec (-RegenerateSpec): $SpecPath"
    }

    if (-not (Test-Path $SpecPath)) {
        $SpecDir = Split-Path -Parent $SpecPath
        New-Item -ItemType Directory -Force $SpecDir | Out-Null
        Invoke-CommandChecked "Generate spec" {
            $specArgs = @(
                "-m", "PyInstaller",
                "--noconfirm",
                "--windowed",
                "--name", "RHYME",
                "--specpath", $SpecDir,
                "--collect-submodules", "frontend.apps.desktop.windows",
                "--collect-submodules", "frontend.core",
                "--collect-submodules", "frontend.utils"
            )
            if (Test-Path $IconOutputPath) {
                $specArgs += @("--icon", $IconOutputPath)
            }
            $specArgs += $EntryScript
            python @specArgs
        }
    }

    if ($Clean) {
        if (Test-Path $DistPath) {
            Remove-Item $DistPath -Recurse -Force
            Write-Log "Cleaned dist: $DistPath"
        }
        if (Test-Path $LegacyDistPath) {
            Remove-Item $LegacyDistPath -Recurse -Force
            Write-Log "Cleaned legacy dist: $LegacyDistPath"
        }
        if (Test-Path $LegacyFlatDistPath) {
            Remove-Item $LegacyFlatDistPath -Recurse -Force
            Write-Log "Cleaned legacy dist: $LegacyFlatDistPath"
        }
        if (Test-Path $WorkPath) {
            Remove-Item $WorkPath -Recurse -Force
            Write-Log "Cleaned work: $WorkPath"
        }
        if (Test-Path $LegacyWorkPath) {
            Remove-Item $LegacyWorkPath -Recurse -Force
            Write-Log "Cleaned legacy work: $LegacyWorkPath"
        }
    }

    Invoke-CommandChecked "Run PyInstaller build" {
        python -m PyInstaller --noconfirm --clean --distpath $DistPath --workpath $WorkPath $SpecPath
    }

    Write-Log "Build finished: ${DistPath}\RHYME\RHYME.exe"
}
catch {
    Write-Log "Build failed: $($_.Exception.Message)" "ERROR"
    Write-Log "Last command: $script:LastCommand" "ERROR"
    Write-Log "SpecPath=$SpecPath" "ERROR"
    Write-Log "DistPath=$DistPath" "ERROR"
    Write-Log "WorkPath=$WorkPath" "ERROR"
    throw
}

