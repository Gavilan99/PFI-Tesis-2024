# Step 8 — Build the API image from a git tag or commit and push it to ECR.
#
#     powershell -File backend\infra\08-image.ps1 -Ref v1.0.0
#     powershell -File backend\infra\08-image.ps1 -Ref feature/be-08-deploy
#     powershell -File backend\infra\08-image.ps1 -Ref v1.1.0 -Models C:\ruta\a\artifacts
#     powershell -File backend\infra\08-image.ps1 -Ref HEAD -BuildOnly     # local build, no AWS at all
#
# Builds from `git archive <Ref>`, never from the working tree: what runs is exactly that commit.
# The image tag says what it is: the tag name for a tag (`v1.0.0`), `sha-<commit>` otherwise, plus
# `-models-<hash>` when -Models is given. The image carries the same in its labels.
# Trained models are not versioned: -Models points to the folder train.py wrote (cut_040/, ...), and
# it is copied to backend/app/ml/artifacts/ inside the build context only.
# Tags are immutable in ECR: an image that is already there is not pushed again.
# Prints the tag to pass to 09-service.ps1. Cost: storage only (see 04-registry.ps1).

param(
    [Parameter(Mandatory = $true)][string]$Ref,
    [string]$Models,
    [switch]$BuildOnly
)

. "$PSScriptRoot\_common.ps1"

Step "Ref $Ref"
$ErrorActionPreference = 'Continue'
$commit = (& git -C $RepoRoot rev-parse --verify "$Ref^{commit}" 2>$null)
$isTag = [bool](& git -C $RepoRoot tag --list $Ref)
$ErrorActionPreference = 'Stop'
if (-not $commit) { throw "No existe el ref '$Ref' en este repositorio." }
$short = $commit.Substring(0, 12)
if ($isTag) { $imageTag = $Ref } else { $imageTag = "sha-$short" }
Done "commit $commit$(if ($isTag) { ' (tag)' })"

$modelsHash = 'none'
if ($Models) {
    if (-not (Test-Path -LiteralPath $Models -PathType Container)) { throw "No existe la carpeta de modelos $Models." }
    $files = Get-ChildItem -LiteralPath $Models -Recurse -File | Sort-Object FullName
    if (-not $files) { throw "La carpeta de modelos $Models está vacía." }
    $joined = ($files | ForEach-Object { (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash + ' ' + $_.FullName.Substring($Models.Length) }) -join "`n"
    $sha = [Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($joined))
    $modelsHash = (-join ($sha | ForEach-Object { $_.ToString('x2') })).Substring(0, 12)
    $imageTag = "$imageTag-models-$modelsHash"
    Done "modelos de $Models ($($files.Count) archivos, hash $modelsHash)"
}
$image = "$Registry/${Repository}:$imageTag"

Step "¿Ya está $imageTag en ECR?"
if ($BuildOnly) { Done 'No se consulta (-BuildOnly)' }
elseif (AwsTry ecr describe-images --repository-name $Repository --image-ids "imageTag=$imageTag") {
    Done "Ya está: no se vuelve a construir ni a subir."
    Write-Output $imageTag
    return
}

Step 'Contexto de build limpio (git archive)'
$context = Join-Path ([IO.Path]::GetTempPath()) "nureon-build-$short"
if (Test-Path $context) { Remove-Item -Recurse -Force $context }
New-Item -ItemType Directory -Path $context | Out-Null
$tar = Join-Path ([IO.Path]::GetTempPath()) "nureon-build-$short.tar"
& git -C $RepoRoot archive --format=tar -o $tar $commit backend research/bank
if ($LASTEXITCODE -ne 0) { throw 'git archive falló.' }
& tar -xf $tar -C $context
if ($LASTEXITCODE -ne 0) { throw 'No se pudo extraer el archivo.' }
Remove-Item -Force $tar
if ($Models) { Copy-Item -Recurse -LiteralPath $Models -Destination (Join-Path $context 'backend\app\ml\artifacts') }
Done $context

try {
    Step "docker build $image"
    & docker build -f (Join-Path $context 'backend\Dockerfile') --build-arg "GIT_REF=$Ref@$short" `
        --label "org.opencontainers.image.revision=$commit" --label "nureon.ref=$Ref" --label "nureon.models=$modelsHash" `
        -t $image $context
    if ($LASTEXITCODE -ne 0) { throw 'docker build falló.' }
    if ($BuildOnly) { Done "Construida $image (sin subir)"; Write-Output $imageTag; return }

    Step 'docker login en ECR y push'
    # The password goes from the CLI to docker through the pipe, never to the screen.
    $ErrorActionPreference = 'Continue'
    & $AwsExe ecr get-login-password --profile $AwsProfile --region $Region | & docker login --username AWS --password-stdin $Registry
    $ErrorActionPreference = 'Stop'
    if ($LASTEXITCODE -ne 0) { throw 'docker login falló.' }
    & docker push $image
    if ($LASTEXITCODE -ne 0) { throw 'docker push falló.' }
    & docker logout $Registry | Out-Null
} finally {
    Remove-Item -Recurse -Force $context -ErrorAction SilentlyContinue
}
Done "Subida $image"
Write-Output $imageTag
