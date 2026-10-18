# Turn everything off so it stops costing money. Deletes what steps 1-11 created, in reverse.
#
#     powershell -File backend\infra\teardown.ps1 -Confirm apagar-nureon
#     powershell -File backend\infra\teardown.ps1 -Confirm apagar-nureon -SkipFinalSnapshot
#
# The database leaves a final snapshot (nureon-db-final-<date>) unless -SkipFinalSnapshot: it keeps
# the pilot's data and costs US$0.095 per GB-month of snapshot (under US$2 a month at 20 GB). Delete it
# by hand when it is no longer needed. Not touched: the Cognito user pool and the SES identity (they
# predate this and cost nothing), and the IAM user nureon-deploy.
# Re-runnable: what is already gone is skipped. Takes ~20 minutes (RDS and CloudFront are slow).

param(
    [Parameter(Mandatory = $true)][string]$Confirm,
    [switch]$SkipFinalSnapshot
)

. "$PSScriptRoot\_common.ps1"
if ($Confirm -ne 'apagar-nureon') { throw 'Para borrar todo, pasá -Confirm apagar-nureon.' }

$dbSg = Get-SecurityGroupId $DbSecurityGroup

Step 'Reglas de la base que nombran al servicio (si no, Express Mode no puede borrar su security group)'
if ($dbSg) {
    $rules = Aws ec2 describe-security-groups --group-ids $dbSg --query 'SecurityGroups[0].IpPermissions'
    if (@($rules).Count) { Aws ec2 revoke-security-group-ingress --group-id $dbSg --ip-permissions (JsonArg @($rules)) | Out-Null; Done 'Quitadas' }
    else { Done 'No hay' }
}

Step "Servicio $Service (Express Mode borra su ALB, target group, security groups y certificado)"
if (Get-ExpressService) {
    Aws ecs delete-express-gateway-service --service-arn (Get-ServiceArn) | Out-Null
    for ($i = 0; $i -lt 60 -and (Get-ExpressService); $i++) { Start-Sleep -Seconds 20 }
    if (Get-ExpressService) { throw 'El servicio no terminó de borrarse en 20 minutos: volvé a correr el script.' }
    Done 'Borrado'
} else { Done 'No existe' }

Step "Cluster $Cluster"
if ((AwsTry ecs describe-clusters --clusters $Cluster --query 'clusters[0].status') -eq 'ACTIVE') {
    foreach ($t in @(Aws ecs list-tasks --cluster $Cluster --query 'taskArns')) { if ($t) { Aws ecs stop-task --cluster $Cluster --task $t | Out-Null } }
    Aws ecs delete-cluster --cluster $Cluster | Out-Null
    Done 'Borrado'
} else { Done 'No existe' }

Step "Base $DbInstance"
$db = Get-DbInstance
if ($db) {
    if ($db.DeletionProtection) {
        Aws rds modify-db-instance --db-instance-identifier $DbInstance --no-deletion-protection --apply-immediately | Out-Null
        Aws rds wait db-instance-available --db-instance-identifier $DbInstance | Out-Null
    }
    if ($SkipFinalSnapshot) {
        Aws rds delete-db-instance --db-instance-identifier $DbInstance --skip-final-snapshot --delete-automated-backups | Out-Null
    } else {
        $snapshot = "nureon-db-final-$((Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmm'))"
        Aws rds delete-db-instance --db-instance-identifier $DbInstance --final-db-snapshot-identifier $snapshot --delete-automated-backups | Out-Null
        Done "Snapshot final: $snapshot"
    }
    Done 'Borrándose (~10 min); su secreto maestro se borra con ella...'
    Aws rds wait db-instance-deleted --db-instance-identifier $DbInstance | Out-Null
    Done 'Borrada'
} else { Done 'No existe' }

Step 'Red de la base'
if (AwsTry rds describe-db-subnet-groups --db-subnet-group-name $DbSubnetGroup) {
    Aws rds delete-db-subnet-group --db-subnet-group-name $DbSubnetGroup | Out-Null; Done "DB subnet group $DbSubnetGroup borrado"
}
if ($dbSg) { Aws ec2 delete-security-group --group-id $dbSg | Out-Null; Done "Security group $dbSg borrado" }
foreach ($id in @(Aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VpcId" 'Name=tag:Project,Values=nureon' --query 'Subnets[].SubnetId')) {
    if ($id) { Aws ec2 delete-subnet --subnet-id $id | Out-Null; Done "Subnet $id borrada" }
}
$rt = Aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VpcId" "Name=tag:Name,Values=$PrivateRouteTable" --query 'RouteTables[0].RouteTableId'
if ($rt) { Aws ec2 delete-route-table --route-table-id $rt | Out-Null; Done "Tabla de rutas $rt borrada" }

Step "Secreto $AppSecretName (recuperable 7 días)"
if (Get-AppSecretArn) { Aws secretsmanager delete-secret --secret-id $AppSecretName --recovery-window-in-days 7 | Out-Null; Done 'Programado para borrar' }
else { Done 'No existe' }

Step "Repositorio $Repository y log group"
if (AwsTry ecr describe-repositories --repository-names $Repository) { Aws ecr delete-repository --repository-name $Repository --force | Out-Null; Done 'Repositorio borrado' }
if (@(Aws logs describe-log-groups --log-group-name-prefix $LogGroup --query 'logGroups[].logGroupName') -contains $LogGroup) {
    Aws logs delete-log-group --log-group-name $LogGroup | Out-Null; Done 'Log group borrado'
}

Step 'Roles'
foreach ($role in @($ExecutionRole, $TaskRole, $InfraRole)) {
    if (-not (AwsTry iam get-role --role-name $role)) { continue }
    foreach ($p in @(Aws iam list-role-policies --role-name $role --query 'PolicyNames')) { if ($p) { Aws iam delete-role-policy --role-name $role --policy-name $p | Out-Null } }
    foreach ($p in @(Aws iam list-attached-role-policies --role-name $role --query 'AttachedPolicies[].PolicyArn')) { if ($p) { Aws iam detach-role-policy --role-name $role --policy-arn $p | Out-Null } }
    Aws iam delete-role --role-name $role | Out-Null
    Done "$role borrado"
}

Step 'Frontend: CloudFront (deshabilitar, esperar, borrar), OAC y bucket'
$dist = Get-Distribution
if ($dist) {
    $cfg = Aws cloudfront get-distribution-config --id $dist.Id
    if ($cfg.DistributionConfig.Enabled) {
        $cfg.DistributionConfig.Enabled = $false
        Aws cloudfront update-distribution --id $dist.Id --if-match $cfg.ETag --distribution-config (JsonArg $cfg.DistributionConfig) | Out-Null
        Done 'Deshabilitada; esperando a que se propague (~5-15 min)...'
    }
    Aws cloudfront wait distribution-deployed --id $dist.Id | Out-Null
    $etag = Aws cloudfront get-distribution-config --id $dist.Id --query 'ETag'
    Aws cloudfront delete-distribution --id $dist.Id --if-match $etag | Out-Null
    Done "Distribución $($dist.Id) borrada"
}
$oac = @(Aws cloudfront list-origin-access-controls --query 'OriginAccessControlList.Items[]' | Where-Object { $_.Name -eq $FrontendOac })[0]
if ($oac) {
    $etag = Aws cloudfront get-origin-access-control --id $oac.Id --query 'ETag'
    Aws cloudfront delete-origin-access-control --id $oac.Id --if-match $etag | Out-Null
    Done 'OAC borrado'
}
if (AwsTry s3api head-bucket --bucket $FrontendBucket) {
    Aws s3 rm "s3://$FrontendBucket" --recursive | Out-Null
    Aws s3api delete-bucket --bucket $FrontendBucket | Out-Null
    Done 'Bucket vaciado y borrado'
}
Remove-TempFiles

Step 'Listo. Lo que queda:'
& "$PSScriptRoot\status.ps1"
