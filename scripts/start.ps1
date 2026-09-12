param([ValidateSet('api','web')][string]$Service)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
if ($Service -eq 'api') {
  Set-Location (Join-Path $TaskRoot 'services/api')
  & '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --host localhost --port 8000 --no-access-log --no-proxy-headers
} elseif ($Service -eq 'web') {
  Set-Location (Join-Path $TaskRoot 'apps/web')
  npm run start
} else {
  throw 'Choose -Service api or -Service web; run each in its own terminal.'
}
exit $LASTEXITCODE
