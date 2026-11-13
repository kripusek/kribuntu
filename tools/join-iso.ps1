param([string]$Directory = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
$base = 'kribuntu-26.04.1-experimental.iso'
$parts = @(Get-ChildItem -LiteralPath $Directory -Filter "$base.part-*" | Sort-Object Name)
if ($parts.Count -eq 0) { throw 'Nie znaleziono części ISO. Pobierz wszystkie części wydania do jednego folderu.' }
$hashFile = Join-Path $Directory "$base.sha256"
if (-not (Test-Path -LiteralPath $hashFile)) { throw 'Brakuje pliku sumy kontrolnej ISO.' }
$expected = ((Get-Content -LiteralPath $hashFile -First 1) -split '\s+')[0].ToLowerInvariant()
$outPath = Join-Path $Directory $base
if (Test-Path -LiteralPath $outPath) { throw "Plik $outPath już istnieje. Usuń go lub przenieś przed ponownym łączeniem." }
$out = [System.IO.File]::Create($outPath)
try {
    foreach ($part in $parts) {
        Write-Host "Łączę $($part.Name)..."
        $inputStream = [System.IO.File]::OpenRead($part.FullName)
        try { $inputStream.CopyTo($out) } finally { $inputStream.Dispose() }
    }
} finally { $out.Dispose() }
Write-Host 'Sprawdzam sumę SHA-256...'
$actual = (Get-FileHash -LiteralPath $outPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw 'Suma się nie zgadza. Pobierz wszystkie części ponownie; wynikowego ISO nie używaj.' }
Write-Host "Gotowe: $outPath"
