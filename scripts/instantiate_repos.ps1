# Parse the YAML file
# Note: PowerShell doesn't have native YAML parsing without a module, 
# so we will use a simple regex/string parsing trick to extract 'id:' fields.

$YamlPath = ".\configs\REPO_MAP.yaml"
$Content = Get-Content $YamlPath

Write-Host "Initializing Maroon Ecosystem Locally..."

foreach ($Line in $Content) {
    if ($Line -match "\s*- id:\s*(.+)") {
        $RepoName = $Matches[1].Trim(' "''')
        Write-Host "Scaffolding Repository: $RepoName"
        
        # 1. Create the Local Repo Directory
        $RepoPath = ".\$RepoName"
        if (-Not (Test-Path $RepoPath)) {
            New-Item -ItemType Directory -Path $RepoPath -Force | Out-Null
        }
        
        # 2. Apply Maroon Codex Standard Folder Structure
        $Folders = @("src", "docs", "scripts", "configs", "tests", ".github\workflows")
        foreach ($Folder in $Folders) {
            $FolderPath = Join-Path $RepoPath $Folder
            New-Item -ItemType Directory -Path $FolderPath -Force | Out-Null
            # touch .gitkeep
            New-Item -ItemType File -Path (Join-Path $FolderPath ".gitkeep") -Force | Out-Null
        }
        
        # 3. Create essential project files
        $ReadmePath = Join-Path $RepoPath "README.md"
        "# $RepoName" | Out-File -FilePath $ReadmePath -Encoding utf8
        "## Part of the Maroon Ecosystem v3.0" | Out-File -FilePath $ReadmePath -Encoding utf8 -Append
        
        # 4. Initialize Local Git
        Set-Location $RepoPath
        git init | Out-Null
        git add . | Out-Null
        git commit -m "SYSTEM: Initialize Maroon Codex Standard Structure" | Out-Null
        Set-Location ..
        
        Write-Host "Success: $RepoName instantiated."
    }
}

Write-Host "All repositories created locally. The Empire is online."
