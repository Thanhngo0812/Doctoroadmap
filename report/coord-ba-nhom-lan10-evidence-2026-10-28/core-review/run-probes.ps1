param([string]$Label='baseline',[string]$Selection='', [string]$TestFile='test_independent_admin.py')
$ErrorActionPreference = 'Stop'
$scratchRoot = $PSScriptRoot
$projectRoot = Split-Path -Parent (Split-Path -Parent $scratchRoot)
$pythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
$receiptRoot = Join-Path $scratchRoot 'runs'
New-Item -ItemType Directory -Path $receiptRoot -Force | Out-Null
$env:WAYFINDER_TEST_DATABASE_URL = 'sqlite+pysqlite:///:memory:'
$env:PYTHONDONTWRITEBYTECODE = '1'
$arguments = @('scripts/w05_run_tests.py','-o','addopts=','-q',$TestFile,
    "--basetemp=tmp/probes-$Label","--junitxml=runs/$Label.xml")
if ($Selection) { $arguments += @('-k',$Selection) }
$sourceHashes = @{}
Get-ChildItem -LiteralPath (Join-Path $scratchRoot 'src/web/backend/wayfinder') -Filter '*.py' -Recurse -File |
    ForEach-Object { $sourceHashes[$_.FullName.Substring($scratchRoot.Length + 1).Replace('\','/')] =
        (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() }
$timer = [System.Diagnostics.Stopwatch]::StartNew()
Push-Location -LiteralPath $scratchRoot
try {
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $pythonPath @arguments *> (Join-Path $receiptRoot "$Label.log")
    $nativeExit = $LASTEXITCODE
    $ErrorActionPreference = $oldPreference
} finally { Pop-Location }
$timer.Stop()
$receipt = [ordered]@{label=$Label; command=@($pythonPath)+$arguments; cwd=$scratchRoot;
    native_exit=$nativeExit; seconds=$timer.Elapsed.TotalSeconds; offline=$true;
    database='SQLite synthetic only; no PostgreSQL connection';source_sha256=$sourceHashes}
$receipt | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $receiptRoot "$Label-exit.json")
Get-Content -LiteralPath (Join-Path $receiptRoot "$Label.log") -Tail 40
Write-Output "native_exit=$nativeExit"
exit $nativeExit
