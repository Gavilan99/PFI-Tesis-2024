# Shared names and helpers for the deployment scripts. Dot-sourced at the top of each one:
#
#     . "$PSScriptRoot\_common.ps1"
#
# Windows PowerShell 5.1. Every AWS call goes through `Aws` / `AwsTry`, which always add the deploy
# profile and the region: nothing here can fall back to the `default` profile. JSON parameters go
# through files (`JsonArg`), because PowerShell 5.1 mangles quotes passed to native programs.

$ErrorActionPreference = 'Stop'

# --- account ------------------------------------------------------------------------------------
$AwsProfile = 'nureon-deploy'   # IAM user nureon-deploy, policy in iam/nureon-deployer-policy.json
$Region     = 'us-east-2'       # the only Region the account allows
$AccountId  = '517207997735'

# --- existing resources, reused (docs/aws-setup.md) --------------------------------------------
$VpcId          = 'vpc-0394b415294cc4b43'       # default VPC
# Default public subnets for the service and its ALB: two zones, one public IPv4 per zone for the ALB.
$PublicSubnets  = @('subnet-0bde8ebf69a248f63', 'subnet-0cfe4aca402501801')   # us-east-2a, us-east-2b
$UserPoolId     = 'us-east-2_ZllTXy0w0'
$AppClientId    = '216kporbavdvjbtthon6p28vel'

# --- names of what these scripts create ---------------------------------------------------------
$Tag              = @{ Key = 'Project'; Value = 'nureon' }
$PrivateRouteTable = 'nureon-private'
$DbSecurityGroup  = 'nureon-db'
$DbSubnetGroup    = 'nureon-db'
$DbInstance       = 'nureon-db'
$DbName           = 'nureon'
$DbMasterUser     = 'nureon_admin'
$AppSecretName    = 'nureon/prod/app'           # {"SECRET_KEY": ...}
$Repository       = 'nureon-api'
$Cluster          = 'nureon'
$Service          = 'nureon-api'
$LogGroup         = '/aws/ecs/nureon/nureon-api'
$ExecutionRole    = 'nureon-ecs-execution'
$TaskRole         = 'nureon-ecs-task'
$InfraRole        = 'nureon-ecs-infrastructure'
$FrontendBucket   = "nureon-frontend-$AccountId"
$FrontendOac      = 'nureon-frontend'
$DistributionNote = 'nureon-frontend'           # the distribution's Comment, used to find it
$ContainerPort    = 8000
$BankCsvInImage   = 'bank/NureonAI Prototype v4.1.2.csv'

# The CLI executable itself: inside these scripts the name `aws` is the helper function below.
$AwsExe = (Get-Command aws -CommandType Application | Select-Object -First 1).Source

$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$Registry = "$AccountId.dkr.ecr.$Region.amazonaws.com"

# --- helpers ------------------------------------------------------------------------------------

function Invoke-AwsCli([string[]]$Arguments, [switch]$Quiet) {
    $ErrorActionPreference = 'Continue'   # native stderr must not become a terminating error in 5.1
    $all = $Arguments + @('--profile', $AwsProfile, '--region', $Region, '--output', 'json')
    if ($Quiet) { $out = & $AwsExe @all 2>$null } else { $out = & $AwsExe @all }
    $code = $LASTEXITCODE
    $text = ($out | Out-String).Trim()
    $parsed = $null
    if ($text) { try { $parsed = $text | ConvertFrom-Json } catch { $parsed = $text } }
    return @{ Code = $code; Result = $parsed }
}

# Runs an AWS CLI call and returns its parsed JSON. Stops the script if it fails.
function Aws {
    $r = Invoke-AwsCli -Arguments $args
    if ($r.Code -ne 0) { throw "Falló: aws $($args -join ' ')" }
    return $r.Result
}

# Same, but returns $null on failure without printing the error: for "does it exist yet?" checks.
function AwsTry {
    $r = Invoke-AwsCli -Arguments $args -Quiet
    if ($r.Code -ne 0) { return $null }
    return $r.Result
}

# Writes an object as JSON (UTF-8 without BOM) to a temp file and returns "file://<path>".
function JsonArg($Object) {
    $path = [IO.Path]::Combine([IO.Path]::GetTempPath(), "nureon-$([guid]::NewGuid().ToString('N')).json")
    $json = $Object | ConvertTo-Json -Depth 20 -Compress
    [IO.File]::WriteAllText($path, $json, (New-Object Text.UTF8Encoding($false)))
    $script:TempFiles += , $path
    return "file://$path"
}
$script:TempFiles = @()
function Remove-TempFiles { foreach ($f in $script:TempFiles) { Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue } }

# A value from backend/.env (local, never committed), e.g. the contact inbox.
function Get-DotEnv([string]$Name) {
    $envFile = Join-Path $RepoRoot 'backend\.env'
    $line = Get-Content -LiteralPath $envFile -Encoding UTF8 | Where-Object { $_ -match "^\s*$Name\s*=" } | Select-Object -Last 1
    if (-not $line) { throw "Falta $Name en backend/.env." }
    $value = ($line -split '=', 2)[1].Trim().Trim('"').Trim("'")
    if (-not $value) { throw "$Name está vacío en backend/.env." }
    return $value
}

function Step([string]$Message) { Write-Host "`n== $Message" -ForegroundColor Cyan }
function Done([string]$Message) { Write-Host "   $Message" -ForegroundColor Green }

# --- lookups shared by several scripts ----------------------------------------------------------

function Get-SecurityGroupId([string]$Name) {
    # JSON null (no such group) parses to $null.
    return Aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VpcId" "Name=group-name,Values=$Name" --query 'SecurityGroups[0].GroupId'
}

function Get-DbInstance { return AwsTry rds describe-db-instances --db-instance-identifier $DbInstance --query 'DBInstances[0]' }

function Get-AppSecretArn { return AwsTry secretsmanager describe-secret --secret-id $AppSecretName --query 'ARN' }

function Get-ServiceArn { return "arn:aws:ecs:${Region}:${AccountId}:service/$Cluster/$Service" }

function Get-ExpressService {
    $svc = AwsTry ecs describe-express-gateway-service --service-arn (Get-ServiceArn) --query 'service'
    if ($svc -and $svc.status.statusCode -ne 'INACTIVE') { return $svc }
    return $null
}

function Get-ServiceUrl {
    $svc = Get-ExpressService
    if (-not $svc) { return $null }
    $endpoint = @($svc.activeConfigurations | ForEach-Object { $_.ingressPaths } |
        Where-Object { $_.accessType -eq 'PUBLIC' } | ForEach-Object { $_.endpoint })[0]
    if (-not $endpoint) { return $null }
    if ($endpoint -notmatch '^https?://') { $endpoint = "https://$endpoint" }
    return $endpoint.TrimEnd('/')
}

# The ECS service behind the Express service: its task definition and the security group Express made.
function Get-EcsService {
    return AwsTry ecs describe-services --cluster $Cluster --services $Service --query 'services[0]'
}

function Get-Distribution {
    $list = Aws cloudfront list-distributions --query 'DistributionList.Items[].{Id:Id,Arn:ARN,Domain:DomainName,Comment:Comment,Status:Status,Enabled:Enabled}'
    return @($list | Where-Object { $_.Comment -eq $DistributionNote })[0]
}
