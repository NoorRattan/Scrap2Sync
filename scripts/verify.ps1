$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$Results = [System.Collections.Generic.List[object]]::new()
function Invoke-Check([string]$Label, [string]$Directory, [string]$Executable, [string[]]$Arguments) {
  Push-Location $Directory
  try {
    Write-Output "Checking: $Label"
    & $Executable @Arguments
    $Code = $LASTEXITCODE
    $Results.Add([pscustomobject]@{ check=$Label; command=($Executable + ' ' + ($Arguments -join ' ')); result=$(if ($Code -eq 0) {'pass'} else {'fail'}); exitCode=$Code; checkedAt=(Get-Date).ToUniversalTime().ToString('o') })
    if ($Code -ne 0) { throw "Verification failed: $Label" }
  } finally { Pop-Location }
}
try {
  $ApiPath = Join-Path $TaskRoot 'services/api'
  $WebPath = Join-Path $TaskRoot 'apps/web'
  Invoke-Check 'Locked backend sync' $ApiPath 'uv' @('sync','--frozen')
  Invoke-Check 'Backend formatting' $ApiPath 'uv' @('run','--frozen','ruff','format','--check','app','tests')
  Invoke-Check 'Backend lint and static checks' $ApiPath 'uv' @('run','--frozen','ruff','check','app','tests')
  Invoke-Check 'Backend strict typing' $ApiPath 'uv' @('run','--frozen','mypy','app')
  Invoke-Check 'Backend behavioral tests and coverage' $ApiPath 'uv' @('run','--frozen','python','-m','pytest','--cov=app','--cov-report=term-missing','--cov-report=xml')
  Invoke-Check 'Generated OpenAPI drift' $ApiPath 'uv' @('run','--frozen','python','-m','app.export_openapi','--check')
  Invoke-Check 'Backend dependency audit' $ApiPath 'uv' @('run','--frozen','pip-audit')
  Invoke-Check 'Frontend formatting' $WebPath 'npm' @('run','format:check')
  Invoke-Check 'Frontend lint' $WebPath 'npm' @('run','lint')
  Invoke-Check 'Frontend strict typing' $WebPath 'npm' @('run','typecheck')
  Invoke-Check 'Frontend generated contract drift' $WebPath 'npm' @('run','contract:check')
  Invoke-Check 'Frontend component tests and coverage' $WebPath 'npm' @('run','test:coverage')
  Invoke-Check 'Frontend production build' $WebPath 'npm' @('run','build')
  Invoke-Check 'Frontend dependency audit' $WebPath 'npm' @('audit','--audit-level=high')
  Invoke-Check 'Workflow lint' $TaskRoot (Join-Path $TaskRoot '.tools/actionlint/actionlint.exe') @()
  Invoke-Check 'Repository structural scan' $TaskRoot (Join-Path $ApiPath '.venv/Scripts/python.exe') @('scripts/security_scan.py')
} finally {
  $ReportPath = Join-Path $TaskRoot 'docs/reports'
  New-Item -ItemType Directory -Path $ReportPath -Force | Out-Null
  $Results | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $ReportPath 'local-checks.json') -Encoding utf8
}
Write-Output 'Checks passed. Run browser tests against the local API, benchmark, and profiling separately.'
