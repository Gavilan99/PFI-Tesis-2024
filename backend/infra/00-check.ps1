# Read-only checks before creating anything. Creates nothing, costs nothing.
#
#     powershell -File backend\infra\00-check.ps1
#
# Stops on the first service that refuses a read call, and says which.

. "$PSScriptRoot\_common.ps1"

Step 'Identidad y plan de la cuenta'
$me = Aws sts get-caller-identity
if ($me.Arn -ne "arn:aws:iam::${AccountId}:user/nureon-deploy") { throw "Perfil inesperado: $($me.Arn)" }
Done $me.Arn
$plan = Aws freetier get-account-plan-state
Done ("Plan {0} ({1}); créditos restantes US$ {2}; vence {3}" -f $plan.accountPlanType, $plan.accountPlanStatus,
    $plan.accountPlanRemainingCredits.amount, $plan.accountPlanExpirationDate)

Step 'AWS CLI con Express Mode'
$ErrorActionPreference = 'Continue'
& $AwsExe ecs create-express-gateway-service help *> $null
if ($LASTEXITCODE -ne 0) { throw 'Esta AWS CLI no trae create-express-gateway-service: actualizala.' }
$ErrorActionPreference = 'Stop'
Done (& $AwsExe --version)

Step 'Cada servicio responde en us-east-2 (sólo lectura)'
$checks = [ordered]@{
    'ECS'             = @('ecs', 'list-clusters')
    'ECR'             = @('ecr', 'describe-repositories')
    'RDS'             = @('rds', 'describe-db-instances')
    'EC2/VPC'         = @('ec2', 'describe-vpcs', '--vpc-ids', $VpcId)
    'ELB'             = @('elbv2', 'describe-load-balancers')
    'CloudFront'      = @('cloudfront', 'list-distributions')
    'S3'              = @('s3api', 'list-buckets')
    'Secrets Manager' = @('secretsmanager', 'list-secrets')
    'CloudWatch Logs' = @('logs', 'describe-log-groups', '--limit', '1')
    'ACM'             = @('acm', 'list-certificates')
}
foreach ($name in $checks.Keys) {
    $r = Invoke-AwsCli -Arguments $checks[$name]
    if ($r.Code -ne 0) { throw "$name no responde: revisá el error de arriba." }
    Done "$name OK"
}

Step 'Express Mode: la API existe (un ARN inexistente tiene que dar "not found", no "access denied")'
$ErrorActionPreference = 'Continue'
$probe = & $AwsExe ecs describe-express-gateway-service --service-arn "arn:aws:ecs:${Region}:${AccountId}:service/nureon-probe/none" --profile $AwsProfile --region $Region 2>&1 | Out-String
$ErrorActionPreference = 'Stop'
if ($probe -match 'AccessDenied|not authorized|explicit deny') { throw "Express Mode bloqueado: $probe" }
Done 'Express Mode disponible'

Step 'Crear red, sin crear nada (--dry-run)'
foreach ($call in @(
        @('ec2', 'create-security-group', '--group-name', 'nureon-dryrun', '--description', 'dryrun', '--vpc-id', $VpcId, '--dry-run'),
        @('ec2', 'create-subnet', '--vpc-id', $VpcId, '--cidr-block', '172.31.255.0/28', '--availability-zone', "${Region}a", '--dry-run'))) {
    $ErrorActionPreference = 'Continue'
    $out = & $AwsExe @call --profile $AwsProfile --region $Region 2>&1 | Out-String
    $ErrorActionPreference = 'Stop'
    if ($out -notmatch 'DryRunOperation') { throw "$($call[1]) no se permitiría: $out" }
    Done "$($call[1]) se permitiría"
}

Step 'RDS: PostgreSQL 16 en db.t4g.micro con gp3'
$versions = Aws rds describe-db-engine-versions --engine postgres --engine-version 16 --query 'DBEngineVersions[].EngineVersion'
Done ("Versiones 16.x: " + ($versions -join ', '))
