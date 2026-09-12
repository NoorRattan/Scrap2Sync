$TaskRoot = Split-Path -Parent $PSScriptRoot
$env:NPM_CONFIG_CACHE = Join-Path $TaskRoot '.cache/npm'
$env:UV_CACHE_DIR = Join-Path $TaskRoot '.cache/uv'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $TaskRoot '.tools/python'
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $TaskRoot '.cache/playwright'
$env:TEMP = Join-Path $TaskRoot '.cache/tmp'
$env:TMP = $env:TEMP
$env:NEXT_TELEMETRY_DISABLED = '1'
$env:DO_NOT_TRACK = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:FORMATTER_PROVIDER = 'disabled'
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null
$TaskNode = Join-Path $TaskRoot '.tools/node-v24.20.0-win-x64'
if (Test-Path -LiteralPath $TaskNode) { $env:PATH = $TaskNode + ';' + $env:PATH }
$TaskUv = Join-Path $TaskRoot '.tools/uv/bin'
if (Test-Path -LiteralPath $TaskUv) { $env:PATH = $TaskUv + ';' + $env:PATH }
