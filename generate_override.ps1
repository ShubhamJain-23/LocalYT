$foldersPath = "folders.txt"
if (-not (Test-Path $foldersPath)) {
    New-Item -Path $foldersPath -ItemType File | Out-Null
}

$folders = Get-Content -Path $foldersPath | Where-Object { $_.Trim() -ne '' }

# Create a clean array of unique, unquoted paths
$cleanFolders = @()
foreach ($folder in $folders) {
    $clean = $folder.Trim().Trim('"').Trim("'")
    if ($clean -and $cleanFolders -notcontains $clean) {
        $cleanFolders += $clean
    }
}

# Write them back clean
$cleanFolders | Set-Content -Path $foldersPath

$yaml = "services:`n  backend:`n    volumes:`n"
$dataDirs = @()
$counter = 1

foreach ($folder in $cleanFolders) {
    # YAML needs double backslashes for quoted strings
    $escaped = $folder -replace '\\', '\\'
    $yaml += "      - `"$escaped:/app/data/folder$counter:ro`"`n"
    $dataDirs += "/app/data/folder$counter"
    $counter++
}

$yaml += "    environment:`n"
$yaml += "      - DATA_DIRS=" + ($dataDirs -join ",") + "`n"

Set-Content -Path "docker-compose.override.yml" -Value $yaml
Write-Host "docker-compose updated with $($cleanFolders.Count) folders."
