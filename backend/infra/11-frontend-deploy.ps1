# Step 11 — Build the frontend from a git tag or commit, pointed at the API, and publish it.
#
#     powershell -File backend\infra\11-frontend-deploy.ps1 -Ref v1.0.0
#     powershell -File backend\infra\11-frontend-deploy.ps1 -Ref HEAD -BuildOnly     # no AWS at all
#
# Builds from `git archive <Ref>` (npm ci + ng build --configuration production), with apiBaseUrl set
# to the Express service's URL in that copy only; the repository's environment.ts is not touched.
# Uploads to the bucket:
#   hashed js/css      cached a year (immutable: a new build has new names)
#   assets/, favicon   cached a day
#   every .html        no-cache, and each prerendered route also at its path without a slash
#                      (`/contacto`), so CloudFront finds it without a rewrite function
#   /index.csr.html    the unrendered app shell, served with 200 for any other route (07-frontend-infra)
# then invalidates the distribution. Cost: S3 requests and storage in cents; invalidation free.

param(
    [Parameter(Mandatory = $true)][string]$Ref,
    [string]$ApiUrl,
    [switch]$BuildOnly
)

. "$PSScriptRoot\_common.ps1"

$AppDir = 'frontend/nureon'
$Environment = 'src/environments/environment.ts'

Step "Ref $Ref"
$ErrorActionPreference = 'Continue'
$commit = (& git -C $RepoRoot rev-parse --verify "$Ref^{commit}" 2>$null)
$ErrorActionPreference = 'Stop'
if (-not $commit) { throw "No existe el ref '$Ref' en este repositorio." }
$short = $commit.Substring(0, 12)
Done "commit $commit"

if (-not $ApiUrl) {
    if ($BuildOnly) { $ApiUrl = 'https://api.invalid' }
    else {
        $ApiUrl = Get-ServiceUrl
        if (-not $ApiUrl) { throw 'No hay URL del servicio: corré 09-service.ps1 o pasá -ApiUrl.' }
    }
}
if ($ApiUrl -notmatch '^https://[^/]+$') { throw "apiBaseUrl tiene que ser https://host, sin barra final: '$ApiUrl'." }
Done "apiBaseUrl = $ApiUrl"

$work = Join-Path ([IO.Path]::GetTempPath()) "nureon-frontend-$short"
if (Test-Path $work) { Remove-Item -Recurse -Force $work }
New-Item -ItemType Directory -Path $work | Out-Null
try {
    Step 'Copia limpia (git archive) y apiBaseUrl'
    $tar = "$work.tar"
    & git -C $RepoRoot archive --format=tar -o $tar $commit $AppDir
    if ($LASTEXITCODE -ne 0) { throw 'git archive falló.' }
    & tar -xf $tar -C $work
    Remove-Item -Force $tar
    $app = Join-Path $work $AppDir
    $envPath = Join-Path $app $Environment
    $text = [IO.File]::ReadAllText($envPath)
    $pattern = "apiBaseUrl:\s*'[^']*'"
    if (([regex]::Matches($text, $pattern)).Count -ne 1) { throw "No encontré una sola línea apiBaseUrl en $Environment." }
    $text = [regex]::Replace($text, $pattern, "apiBaseUrl: '$ApiUrl'")
    [IO.File]::WriteAllText($envPath, $text, (New-Object Text.UTF8Encoding($false)))
    Done $app

    Step 'npm ci + ng build --configuration production'
    Push-Location $app
    try {
        & npm ci --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw 'npm ci falló.' }
        & npx ng build --configuration production
        if ($LASTEXITCODE -ne 0) { throw 'ng build falló.' }
    } finally { Pop-Location }
    $dist = Join-Path $app 'dist\nureon'
    $browser = Join-Path $dist 'browser'
    $shell = Join-Path $dist 'server\index.server.html'
    if (-not (Test-Path (Join-Path $browser 'index.html'))) { throw 'El build no dejó browser/index.html.' }
    if (-not (Test-Path $shell)) { throw 'El build no dejó server/index.server.html (la plantilla sin prerenderizar).' }
    $routes = @((Get-Content -Raw (Join-Path $dist 'prerendered-routes.json') | ConvertFrom-Json).routes | Where-Object { $_ -ne '/' } |
        ForEach-Object { $_.TrimStart('/') })
    Done ("Rutas prerenderizadas: /, /" + ($routes -join ', /'))
    if ($BuildOnly) { Done "Construido en $browser (sin subir)"; return }

    $distribution = Get-Distribution
    if (-not $distribution) { throw 'No existe la distribución: corré 07-frontend-infra.ps1.' }
    $bucket = "s3://$FrontendBucket"

    Step "Subida a $bucket"
    $keep = @('--exclude', '*.html', '--exclude', 'assets/*', '--exclude', 'favicon.ico', '--exclude', 'index.csr.html') +
        @($routes | ForEach-Object { @('--exclude', $_) })
    Aws s3 sync $browser $bucket --delete @keep --cache-control 'public,max-age=31536000,immutable' | Out-Null
    Done 'js/css con hash (un año, inmutables)'
    Aws s3 sync (Join-Path $browser 'assets') "$bucket/assets" --delete --cache-control 'public,max-age=86400' | Out-Null
    Aws s3 cp (Join-Path $browser 'favicon.ico') "$bucket/favicon.ico" --cache-control 'public,max-age=86400' | Out-Null
    Done 'assets y favicon (un día)'
    Aws s3 cp $browser $bucket --recursive --exclude '*' --include '*.html' --cache-control 'no-cache' --content-type 'text/html; charset=utf-8' | Out-Null
    foreach ($route in $routes) {
        Aws s3 cp (Join-Path $browser "$route\index.html") "$bucket/$route" --cache-control 'no-cache' --content-type 'text/html; charset=utf-8' | Out-Null
    }
    Aws s3 cp $shell "$bucket/index.csr.html" --cache-control 'no-cache' --content-type 'text/html; charset=utf-8' | Out-Null
    Done 'html sin caché, rutas sin barra final y /index.csr.html'

    Step "Invalidación de $($distribution.Id)"
    $inv = Aws cloudfront create-invalidation --distribution-id $distribution.Id --paths '/*' --query 'Invalidation.Id'
    Done "Pedida $inv"
    Done "Frontend: https://$($distribution.Domain)"
} finally {
    Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
}
