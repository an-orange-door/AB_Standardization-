<#
    Renames U:\Textures\SignsSymbols from opaque codes to descriptive names,
    driven by SignsSymbols_rename_manifest.csv.

    DRY RUN BY DEFAULT. Nothing changes until you pass -Apply.

        .\Rename-SignsSymbols.ps1            # show what would happen
        .\Rename-SignsSymbols.ps1 -Apply     # do it

    The manifest keeps old_name, so the rename is fully reversible:

        .\Rename-SignsSymbols.ps1 -Apply -Revert
#>
param(
    [switch]$Apply,
    [switch]$Revert,
    [string]$Root     = 'U:\Textures\SignsSymbols',
    [string]$Manifest = 'U:\AB_Standardization\SignsSymbols_rename_manifest.csv'
)

if (-not (Test-Path $Manifest)) { throw "Manifest not found: $Manifest" }
if (-not (Test-Path $Root))     { throw "Texture root not found: $Root" }

$rows = Import-Csv $Manifest
Write-Host ("manifest rows : {0}" -f $rows.Count)

$done = 0; $skip = 0; $miss = 0
foreach ($r in $rows) {
    $dir = Join-Path $Root $r.folder
    if ($Revert) { $from = $r.new_name; $to = $r.old_name }
    else         { $from = $r.old_name; $to = $r.new_name }

    $src = Join-Path $dir $from
    $dst = Join-Path $dir $to

    if (-not (Test-Path $src)) {
        if (Test-Path $dst) { $skip++ } else { $miss++; Write-Warning "missing: $src" }
        continue
    }
    if ($Apply) {
        Rename-Item -LiteralPath $src -NewName $to -ErrorAction Stop
    } else {
        Write-Host ("  {0}  ->  {1}" -f $from, $to)
    }
    $done++
}

$verb = if ($Apply) { 'renamed' } else { 'would rename' }
Write-Host ""
Write-Host ("{0}: {1}   already-done: {2}   missing: {3}" -f $verb, $done, $skip, $miss)
if (-not $Apply) { Write-Host "DRY RUN - pass -Apply to make the change." -ForegroundColor Yellow }
