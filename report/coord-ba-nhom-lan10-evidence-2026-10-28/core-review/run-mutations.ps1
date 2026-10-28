$ErrorActionPreference = 'Stop'
$scratchRoot = $PSScriptRoot
$servicePath = Join-Path $scratchRoot 'src/web/backend/wayfinder/application/admin.py'
$storePath = Join-Path $scratchRoot 'src/web/backend/wayfinder/infrastructure/admin_store.py'
$apiPath = Join-Path $scratchRoot 'src/web/backend/wayfinder/api/admin.py'
$mutants = @(
    @{ name='r10-revoke'; path=$servicePath; old='self.store.delete_account_sessions(uid)'; new='pass # R10 mutant'; selection='disable_then_enable' },
    @{ name='r10-last-admin'; path=$servicePath; old='and self.store.admin_count() <= 1'; new='and False'; selection='last_role_admin' },
    @{ name='r10-atomic'; path=$servicePath; old="with self.store.atomic(['admin:users', f'account:{uid}', f'account:{target.email_normalized}']):"; new="with __import__('contextlib').nullcontext():"; selection='transaction_rolls_back' },
    @{ name='r10-audit-meta'; path=$storePath; old="('id','at','actor_id','action','target_kind','target_id','ip')"; new="('id','at','actor_id','action','target_kind','target_id','ip','meta')"; selection='sql_audit_boundary' },
    @{ name='r10-http-dto'; path=$apiPath; old="@router.get('/users',response_model=AdminUsersResponse)"; new="@router.get('/users',response_model=None)"; selection='actual_http_guards' },
    @{ name='r10-after-lock'; path=$servicePath; old="            self.authorize(actor)`r`n            target = self.store.get_account(uid)"; new="            # R10 mutant: stale actor after lock`r`n            target = self.store.get_account(uid)"; selection='after_lock_recheck' }
)
$results = @()
foreach ($mutant in $mutants) {
    $originalBytes = [System.IO.File]::ReadAllBytes($mutant.path)
    $originalSha = (Get-FileHash -LiteralPath $mutant.path -Algorithm SHA256).Hash.ToLower()
    $backupPath = Join-Path $scratchRoot ('runs/'+$mutant.name+'-source-original.bin')
    [System.IO.File]::WriteAllBytes($backupPath,$originalBytes)
    $source = [System.Text.Encoding]::UTF8.GetString($originalBytes)
    if (-not $source.Contains($mutant.old)) {
        $mutant.old = $mutant.old.Replace("`r`n","`n")
        $mutant.new = $mutant.new.Replace("`r`n","`n")
    }
    if (($source.Split(@($mutant.old),[System.StringSplitOptions]::None).Count - 1) -ne 1) {
        throw "Mutation match is not unique: $($mutant.name)"
    }
    try {
        [System.IO.File]::WriteAllText($mutant.path,$source.Replace($mutant.old,$mutant.new),[System.Text.UTF8Encoding]::new($false))
        & powershell.exe -NoProfile -File (Join-Path $scratchRoot 'run-probes.ps1') -Label $mutant.name -Selection $mutant.selection
        $nativeExit = $LASTEXITCODE
        [xml]$xml = Get-Content -Raw -LiteralPath (Join-Path $scratchRoot ('runs/'+$mutant.name+'.xml'))
        $failures = @($xml.SelectNodes('//failure')).Count
        $errors = @($xml.SelectNodes('//error')).Count
        $assertionFailures = @($xml.SelectNodes('//failure') | Where-Object { $_.message -match 'assert|DID NOT RAISE' }).Count
        $results += [ordered]@{name=$mutant.name;selection=$mutant.selection;native_exit=$nativeExit;
            failures=$failures;errors=$errors;assertion_failures=$assertionFailures;source_before_sha256=$originalSha;
            caught=($nativeExit -eq 1 -and $failures -gt 0 -and $errors -eq 0 -and $assertionFailures -eq $failures)}
    } finally {
        [System.IO.File]::WriteAllBytes($mutant.path,$originalBytes)
        $restoredSha = (Get-FileHash -LiteralPath $mutant.path -Algorithm SHA256).Hash.ToLower()
        if ($restoredSha -ne $originalSha) { throw "Restore SHA mismatch: $($mutant.name)" }
    }
    $results[-1].restored_sha256 = $restoredSha
    $results | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $scratchRoot 'mutations.json')
}
if (@($results | Where-Object {-not $_.caught}).Count -gt 0) { throw 'A mutant did not fail by assertion.' }
