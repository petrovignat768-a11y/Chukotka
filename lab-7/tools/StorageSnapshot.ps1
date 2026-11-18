# Запускать только в изолированном тестовом профиле Windows. Это не RFT-тест.
# Сканирует только явно указанные корни; ничего в них не изменяет.
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('before','after_add','after_mark','after_delete','after_close','after_restart')]
    [string]$Phase,
    [Parameter(Mandatory=$true)]
    [string[]]$Roots,
    [Parameter(Mandatory=$true)]
    [string]$EvidenceDir
)
$ErrorActionPreference = 'Stop'

function NormalizePath([string]$p) {
    return [System.IO.Path]::GetFullPath($p).TrimEnd([char[]]@('\','/'))
}
function IsWithin([string]$path, [string]$root) {
    $p = (NormalizePath $path) + '\'
    $r = (NormalizePath $root) + '\'
    return $p.StartsWith($r, [System.StringComparison]::OrdinalIgnoreCase)
}
function WriteRows($rows, [string]$path, [string]$header) {
    if (@($rows).Count -eq 0) {
        Set-Content -LiteralPath $path -Value $header -Encoding UTF8
    } else {
        $rows | Export-Csv -LiteralPath $path -NoTypeInformation -Encoding UTF8
    }
}

$evidence = NormalizePath $EvidenceDir
$normalizedRoots = @($Roots | ForEach-Object { NormalizePath $_ } | Select-Object -Unique)
foreach ($root in $normalizedRoots) {
    if ($root -match '^[A-Za-z]:$') { throw "Scan a dedicated test directory, not an entire drive: $root" }
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw "Root does not exist: $root" }
    if (IsWithin $evidence $root) { throw "EvidenceDir must be outside every scan root: $root" }
}
New-Item -ItemType Directory -Force -Path $evidence | Out-Null
$records = New-Object System.Collections.Generic.List[object]
$errors = New-Object System.Collections.Generic.List[string]
$seen = @{}
foreach ($root in $normalizedRoots) {
    $scanErrors = @()
    # PowerShell 5.1+ does not follow directory symbolic links by default unless requested.
    $files = @(Get-ChildItem -LiteralPath $root -File -Force -Recurse -ErrorAction SilentlyContinue -ErrorVariable +scanErrors)
    foreach ($err in $scanErrors) { $errors.Add("SCAN: $err") }
    foreach ($file in $files) {
        if ($seen.ContainsKey($file.FullName)) { continue }
        $seen[$file.FullName] = $true
        if (($file.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            $errors.Add("SKIPPED REPARSE POINT: $($file.FullName)")
            continue
        }
        try {
            $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256 -ErrorAction Stop).Hash
            $records.Add([pscustomobject]@{
                Path = $file.FullName
                Size = $file.Length
                LastWriteTimeUtc = $file.LastWriteTimeUtc.ToString('o')
                SHA256 = $hash
            })
        } catch { $errors.Add("HASH: $($file.FullName): $($_.Exception.Message)") }
    }
}
$snapshot = Join-Path $evidence ($Phase + '.csv')
WriteRows @($records | Sort-Object Path) $snapshot '"Path","Size","LastWriteTimeUtc","SHA256"'
$meta = @(
    "Phase=$Phase",
    "TimeUtc=$([DateTime]::UtcNow.ToString('o'))",
    "Computer=$env:COMPUTERNAME",
    "User=$env:USERNAME",
    "Roots=$($normalizedRoots -join ' | ')",
    "Count=$($records.Count)",
    "Errors=$($errors.Count)"
)
$meta | Set-Content -LiteralPath (Join-Path $evidence ($Phase + '.meta.txt')) -Encoding UTF8
if ($errors.Count -eq 0) { @('No reported scan/hash errors.') | Set-Content -LiteralPath (Join-Path $evidence ($Phase + '.errors.txt')) -Encoding UTF8 }
else { $errors | Set-Content -LiteralPath (Join-Path $evidence ($Phase + '.errors.txt')) -Encoding UTF8 }

$baseline = Join-Path $evidence 'before.csv'
if ($Phase -ne 'before' -and (Test-Path -LiteralPath $baseline)) {
    $old = @{}; $new = @{}
    foreach ($r in @(Import-Csv -LiteralPath $baseline)) { $old[$r.Path] = $r }
    foreach ($r in @(Import-Csv -LiteralPath $snapshot)) { $new[$r.Path] = $r }
    $changes = New-Object System.Collections.Generic.List[object]
    foreach ($path in @((@($old.Keys) + @($new.Keys)) | Sort-Object -Unique)) {
        $kind = $null
        if (-not $old.ContainsKey($path)) { $kind = 'CREATED' }
        elseif (-not $new.ContainsKey($path)) { $kind = 'DELETED' }
        elseif ($old[$path].SHA256 -ne $new[$path].SHA256 -or $old[$path].Size -ne $new[$path].Size) { $kind = 'CONTENT_CHANGED' }
        elseif ($old[$path].LastWriteTimeUtc -ne $new[$path].LastWriteTimeUtc) { $kind = 'METADATA_CHANGED' }
        if ($kind) { $changes.Add([pscustomobject]@{ Change=$kind; Path=$path; BeforeSHA256=$old[$path].SHA256; AfterSHA256=$new[$path].SHA256 }) }
    }
    WriteRows @($changes) (Join-Path $evidence ("changes_before_$Phase.csv")) '"Change","Path","BeforeSHA256","AfterSHA256"'
}
elseif ($Phase -ne 'before') { Write-Warning 'No baseline snapshot: changes were not compared.' }
Write-Output "Snapshot: $snapshot; files=$($records.Count); scan/hash errors=$($errors.Count)."
if ($errors.Count -gt 0) { Write-Warning 'Results are incomplete. Inspect the .errors.txt file.' }
