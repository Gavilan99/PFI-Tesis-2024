# Step 4 — ECR repository for the API image.
#
#     powershell -File backend\infra\04-registry.ps1
#
# Immutable tags (a tag always names the same image: the tag or commit it was built from), scan on
# push, and a lifecycle rule that keeps the last 10 images.
# Cost: US$0.10 per GB-month stored; 10 images of ~0.25 GB compressed, under US$0.30/month.

. "$PSScriptRoot\_common.ps1"

$KeepImages = 10

Step "Repositorio $Repository"
if (-not (AwsTry ecr describe-repositories --repository-names $Repository)) {
    Aws ecr create-repository --repository-name $Repository --image-tag-mutability IMMUTABLE `
        --image-scanning-configuration scanOnPush=true --encryption-configuration encryptionType=AES256 `
        --tags "Key=$($Tag.Key),Value=$($Tag.Value)" | Out-Null
    Done "Creado $Registry/$Repository"
} else { Done "Ya existe $Registry/$Repository" }

Step "Ciclo de vida: quedan las últimas $KeepImages imágenes"
$policy = @{ rules = @(@{
            rulePriority = 1
            description  = "Keep the last $KeepImages images"
            selection    = @{ tagStatus = 'any'; countType = 'imageCountMoreThan'; countNumber = $KeepImages }
            action       = @{ type = 'expire' }
        }) }
Aws ecr put-lifecycle-policy --repository-name $Repository --lifecycle-policy-text (JsonArg $policy) | Out-Null
Remove-TempFiles
Done 'Aplicado'
