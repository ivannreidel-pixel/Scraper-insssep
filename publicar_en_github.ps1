# Publica el buscador de noticias en internet, GRATIS, con GitHub (repositorio + GitHub Pages + GitHub Actions).
#
# Uso: doble clic en PUBLICAR_EN_GITHUB.bat   (o en PowerShell:  .\publicar_en_github.ps1 -Repo nombre-del-repositorio)
#
# Qué hace (se puede repetir sin problema para volver a subir cambios):
#   1. instala Git y GitHub CLI si faltan (con winget, previa confirmación)
#   2. te pide iniciar sesión en GitHub desde el navegador (si no tenés cuenta, se crea gratis ahí mismo)
#   3. sube estos archivos a un repositorio PÚBLICO tuyo
#   4. activa GitHub Pages y lanza la primera actualización
#   5. al terminar abre la dirección pública del buscador
param([string]$Repo = "buscador-noticias")

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

function Titulo($t) { Write-Host "`n== $t" -ForegroundColor Cyan }
function Fallar($msg) { Write-Host "`n[X] $msg" -ForegroundColor Red; Read-Host "Presioná Enter para cerrar"; exit 1 }
function ActualizarPath { $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User') }

function Instalar($comando, $idWinget, $nombre) {
    if (Get-Command $comando -ErrorAction SilentlyContinue) { Write-Host "  ok: $nombre ya está instalado"; return }
    Write-Host "  Falta $nombre. Se instala con winget (gratis y oficial)."
    $r = Read-Host "  ¿Instalarlo ahora? (S/n)"
    if ($r -match '^(n|no)$') { Fallar "$nombre es necesario para publicar." }
    winget install --id $idWinget -e --accept-package-agreements --accept-source-agreements
    ActualizarPath
    if (-not (Get-Command $comando -ErrorAction SilentlyContinue)) {
        Fallar "No se pudo instalar $nombre. Cerrá esta ventana, volvé a abrirla y reintentá."
    }
}

Write-Host "=======================================================" -ForegroundColor Green
Write-Host "  PUBLICAR EL BUSCADOR DE NOTICIAS EN INTERNET (gratis)" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Green
Write-Host "El sitio quedará en un repositorio PÚBLICO de tu cuenta de GitHub y se actualizará solo cada 3 horas."

Titulo "1/6  Programas necesarios"
ActualizarPath
Instalar "git" "Git.Git" "Git"
Instalar "gh" "GitHub.cli" "GitHub CLI"

Titulo "2/6  Cuenta de GitHub"
$estado = (gh auth status 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Se va a abrir el navegador: iniciá sesión en GitHub (o creá tu cuenta gratis) y autorizá el acceso."
    Write-Host "  Si te pide un código, copialo desde esta ventana."
    gh auth login --hostname github.com --git-protocol https --scopes "repo,workflow,read:org" --web
    if ($LASTEXITCODE -ne 0) { Fallar "No se pudo iniciar sesión en GitHub." }
} elseif ($estado -notmatch "workflow") {
    Write-Host "  Se necesita un permiso adicional (workflow) para publicar la actualización automática."
    gh auth refresh --hostname github.com --scopes workflow
}
gh auth setup-git 2>$null | Out-Null
$usuario = (gh api user --jq .login | Out-String).Trim()
$idUsuario = (gh api user --jq .id | Out-String).Trim()
if (-not $usuario) { Fallar "No se pudo leer la cuenta de GitHub." }
Write-Host "  Sesión iniciada como: $usuario"

Titulo "3/6  Preparando los archivos"
if (-not (Test-Path ".git")) { git init -b main | Out-Null }
git config core.autocrlf false                                           # evita avisos de saltos de línea
git config user.name $usuario
git config user.email "$idUsuario+$usuario@users.noreply.github.com"   # correo privado de GitHub: no muestra tu email real
git add -A 2>$null
git commit -m "Buscador de noticias INSSSEP" 2>&1 | Out-Null            # (si no hay cambios, no hace nada)
git branch -M main

Titulo "4/6  Subiendo a GitHub (repositorio público: $usuario/$Repo)"
gh repo view "$usuario/$Repo" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    gh repo create "$usuario/$Repo" --public --description "Buscador de noticias sobre INSSSEP en medios de Chaco" --source . --remote origin --push
    if ($LASTEXITCODE -ne 0) { Fallar "No se pudo crear el repositorio." }
} else {
    if (-not ((git remote) -contains "origin")) { git remote add origin "https://github.com/$usuario/$Repo.git" }
    git push -u origin main
    if ($LASTEXITCODE -ne 0) { Fallar "No se pudo subir a GitHub." }
}

Titulo "5/6  Activando la publicación web (GitHub Pages)"
gh api -X POST "repos/$usuario/$Repo/pages" -f build_type=workflow 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { gh api -X PUT "repos/$usuario/$Repo/pages" -f build_type=workflow 2>$null | Out-Null }
$tipo = (gh api "repos/$usuario/$Repo/pages" --jq .build_type 2>$null | Out-String).Trim()
if ($tipo -eq "workflow") {
    Write-Host "  ok: la publicación web quedó activada"
} else {
    Write-Host "  No se pudo activar automáticamente. Hacelo a mano (1 minuto):" -ForegroundColor Yellow
    Write-Host "    1. Se abre la configuración del repositorio. En 'Build and deployment' > 'Source' elegí: GitHub Actions"
    Write-Host "    2. Volvé a esta ventana y presioná Enter."
    Start-Process "https://github.com/$usuario/$Repo/settings/pages"
    Read-Host "  Presioná Enter cuando lo hayas hecho"
}

Titulo "6/6  Primera actualización (tarda unos 5 a 8 minutos)"
$lanzado = $false
for ($i = 0; $i -lt 10 -and -not $lanzado; $i++) {
    gh workflow run buscar.yml --repo "$usuario/$Repo" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $lanzado = $true } else { Start-Sleep -Seconds 6 }
}
if (-not $lanzado) { Fallar "No se pudo iniciar la actualización. Probá a mano desde: https://github.com/$usuario/$Repo/actions" }
$id = ""
for ($i = 0; $i -lt 15 -and -not $id; $i++) {
    Start-Sleep -Seconds 4
    $id = (gh run list --repo "$usuario/$Repo" --workflow buscar.yml --limit 1 --json databaseId --jq ".[0].databaseId" 2>$null | Out-String).Trim()
}
if (-not $id) { Fallar "No se encontró la actualización. Mirá: https://github.com/$usuario/$Repo/actions" }
Write-Host "  Siguiendo la actualización (no cierres la ventana). Podés ver el avance también en: https://github.com/$usuario/$Repo/actions/runs/$id"
gh run watch $id --repo "$usuario/$Repo" --exit-status
if ($LASTEXITCODE -ne 0) { Fallar "La actualización falló. Detalle en: https://github.com/$usuario/$Repo/actions/runs/$id" }

$url = "https://$($usuario.ToLower()).github.io/$Repo/"
Write-Host "`n=======================================================" -ForegroundColor Green
Write-Host "  LISTO. El buscador ya está en internet:" -ForegroundColor Green
Write-Host "  $url" -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Green
Write-Host "Se abre desde cualquier teléfono o PC y se actualiza solo cada 3 horas."
Write-Host "(Si el navegador muestra «404», esperá 2 o 3 minutos y recargá: la primera vez GitHub tarda un poco en activar la dirección.)"
Write-Host "Administración: https://github.com/$usuario/$Repo"
Set-Clipboard -Value $url -ErrorAction SilentlyContinue
Write-Host "(La dirección quedó copiada: pegala en WhatsApp para compartirla.)"
Start-Process $url
Read-Host "Presioná Enter para cerrar"
