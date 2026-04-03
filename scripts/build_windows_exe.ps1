param(
    [string]$PythonBin = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RootDir

$AppName = "ShotSearch"
$Entry = Join-Path $RootDir "app/main.py"
$ReqFile = Join-Path $RootDir "requirements.txt"
$DistDir = Join-Path $RootDir "dist"
$BuildDir = Join-Path $RootDir "build"
$IconPath = Join-Path $RootDir "packaging/AppIcon.ico"

function Resolve-Python {
    param([string]$Requested)
    if ($Requested -ne "") {
        return $Requested
    }

    $candidates = @("py -3.10", "py -3.11", "python3.10", "python3.11", "python")
    foreach ($c in $candidates) {
        try {
            & cmd /c "$c --version" | Out-Null
            return $c
        } catch {
            continue
        }
    }

    throw "未找到可用 Python，请安装 Python 3.10 或 3.11。"
}

$Py = Resolve-Python -Requested $PythonBin
$Ver = & cmd /c "$Py -c \"import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')\""
$Minor = [int](& cmd /c "$Py -c \"import sys; print(sys.version_info.minor)\"")
if ($Minor -lt 8 -or $Minor -gt 11) {
    throw "当前 Python=$Ver 不受支持。请使用 3.8~3.11（推荐 3.10）。"
}

if (-not (Test-Path $ReqFile)) {
    throw "未找到 requirements.txt: $ReqFile"
}

Write-Host "[INFO] 使用 Python: $Py ($Ver)"

& cmd /c "$Py -m venv .venv"
& .\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
& .\.venv\Scripts\python.exe -m pip install -r $ReqFile pyinstaller

$pyiArgs = @(
    "--name", $AppName,
    "--windowed",
    "--noconfirm",
    "--clean",
    "--add-data", "$RootDir/app;app",
    "--distpath", $DistDir,
    "--workpath", $BuildDir,
    "--specpath", $RootDir
)

if (Test-Path $IconPath) {
    $pyiArgs += @("--icon", $IconPath)
}

& .\.venv\Scripts\pyinstaller.exe @pyiArgs $Entry

$ExePath = Join-Path $DistDir "$AppName\$AppName.exe"
if (-not (Test-Path $ExePath)) {
    throw "未找到 exe 输出：$ExePath"
}

Write-Host "[OK] 打包完成：$ExePath"
Write-Host "[TIP] 将 dist/$AppName 整个目录打包(zip)给用户即可运行。"
