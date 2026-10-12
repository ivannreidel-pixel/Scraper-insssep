# Crea el acceso directo "INSSSEP Scraper" en el Escritorio, que abre el panel de control.
# Uso (PowerShell, en esta carpeta):   .\crear_acceso_directo.ps1
$escritorio = [Environment]::GetFolderPath("Desktop")
$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut((Join-Path $escritorio "INSSSEP Scraper.lnk"))
$lnk.TargetPath = Join-Path $PSScriptRoot "INSSSEP.bat"
$lnk.WorkingDirectory = $PSScriptRoot
$lnk.WindowStyle = 1
$lnk.IconLocation = "$env:SystemRoot\System32\shell32.dll,13"
$lnk.Description = "Abre el panel de control de INSSSEP Scraper"
$lnk.Save()
Write-Host "Acceso directo creado: INSSSEP Scraper"
