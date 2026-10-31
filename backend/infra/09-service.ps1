# Step 9 — The API on ECS Express Mode: creates the service the first time, updates it after.
#
#     powershell -File backend\infra\09-service.ps1 -ImageTag v1.0.0
#     powershell -File backend\infra\09-service.ps1 -ImageTag v1.1.0-models-0123abcd4567 -Classifier trained
#
# Express Mode creates the internet-facing ALB (HTTPS, its own certificate and *.on.aws domain), the
# target group, the scaling policy, and two security groups: the ALB's (443 from anywhere) and the
# service's (the container port only from the ALB's). No security group of ours is passed: one would
# be an extra way in. Tasks run in the default public subnets with a public IP: no NAT gateway.
# Configuration: plain values as environment variables; the database user and password (the RDS
# secret), SECRET_KEY and the two Mercado Pago credentials from Secrets Manager. The plan's price and
# days come from backend/.env (PLAN_INDIVIDUAL_PRICE, PLAN_INDIVIDUAL_DAYS): production has no default. No AWS_PROFILE: credentials come from the task role.
# After the service is stable, the database security group gets its only rule: 5432 from the
# service's security group.
# Cost: Fargate ~US$18/month per task (0.5 vCPU, 1 GB), ALB ~US$17, public IPv4 ~US$11 (2 ALB + 1 task).

param(
    [Parameter(Mandatory = $true)][string]$ImageTag,
    [ValidateSet('stub', 'legacy_tree', 'trained')][string]$Classifier = 'stub',
    # The version of the privacy policy and terms in force, stored with every new account (Feature 11).
    # Same value as LEGAL_TEXT_VERSION in frontend/nureon/src/app/legal/legal-content.ts.
    [string]$ConsentVersion = '2026-10-29'
)

. "$PSScriptRoot\_common.ps1"

$Cpu         = '512'     # 0.5 vCPU
$Memory      = '1024'    # 1 GB
$MinTasks    = 1
$MaxTasks    = 2
$HealthPath  = '/api/health'

Step 'Lo que el servicio necesita'
if (-not (AwsTry ecr describe-images --repository-name $Repository --image-ids "imageTag=$ImageTag")) {
    throw "No está la imagen ${Repository}:$ImageTag en ECR: corré 08-image.ps1."
}
$db = Get-DbInstance
if (-not $db) { throw 'No existe la base: corré 02-database.ps1.' }
$dbSecretArn = $db.MasterUserSecret.SecretArn
$appSecretArn = Get-AppSecretArn
if (-not $appSecretArn) { throw "No existe $AppSecretName`: corré 03-app-secret.ps1." }
$dist = Get-Distribution
if (-not $dist) { throw 'No existe la distribución del frontend: corré 07-frontend-infra.ps1.' }
$roleArn = { param($name) "arn:aws:iam::${AccountId}:role/$name" }
Done "imagen $ImageTag, base $($db.Endpoint.Address), frontend https://$($dist.Domain), clasificador $Classifier"

$environment = [ordered]@{
    APP_ENV               = 'production'
    LOG_LEVEL             = 'INFO'
    CLASSIFIER_BACKEND    = $Classifier
    CORS_ALLOWED_ORIGINS  = "https://$($dist.Domain)"
    TRUSTED_PROXY_HOPS    = '1'
    DB_HOST               = $db.Endpoint.Address
    DB_PORT               = [string]$db.Endpoint.Port
    DB_NAME               = $DbName
    IDENTITY_PROVIDER     = 'cognito'
    COGNITO_REGION        = $Region
    COGNITO_USER_POOL_ID  = $UserPoolId
    COGNITO_APP_CLIENT_ID = $AppClientId
    MAIL_SENDER           = 'ses'
    SES_REGION            = $Region
    CONTACT_MAIL_TO       = (Get-DotEnv 'CONTACT_MAIL_TO')
    CONSENT_VERSION       = $ConsentVersion
    # Feature 17. The personalized description of the paid plan's result.
    TEXT_GENERATOR        = 'bedrock'
    BEDROCK_REGION        = $Region
    BEDROCK_MODEL_ID      = $BedrockModelId
    # Feature 6. The buyer comes back straight to the frontend (HTTPS): no PUBLIC_API_BASE_URL here.
    PAYMENT_PROVIDER      = 'mercadopago'
    FRONTEND_BASE_URL     = "https://$($dist.Domain)"
    PLAN_INDIVIDUAL_PRICE = (Get-DotEnv 'PLAN_INDIVIDUAL_PRICE')
    PLAN_INDIVIDUAL_DAYS  = (Get-DotEnv 'PLAN_INDIVIDUAL_DAYS')
}
$secrets = [ordered]@{
    DB_USER                    = "${dbSecretArn}:username::"
    DB_PASSWORD                = "${dbSecretArn}:password::"
    SECRET_KEY                 = "${appSecretArn}:SECRET_KEY::"
    MERCADOPAGO_ACCESS_TOKEN   = "${appSecretArn}:MERCADOPAGO_ACCESS_TOKEN::"
    MERCADOPAGO_WEBHOOK_SECRET = "${appSecretArn}:MERCADOPAGO_WEBHOOK_SECRET::"
}
$container = @{
    image                = "$Registry/${Repository}:$ImageTag"
    containerPort        = $ContainerPort
    awsLogsConfiguration = @{ logGroup = $LogGroup; logStreamPrefix = 'api' }
    environment          = @($environment.Keys | ForEach-Object { @{ name = $_; value = $environment[$_] } })
    secrets              = @($secrets.Keys | ForEach-Object { @{ name = $_; valueFrom = $secrets[$_] } })
}
$common = @{
    primaryContainer = $container
    executionRoleArn = (& $roleArn $ExecutionRole)
    taskRoleArn      = (& $roleArn $TaskRole)
    healthCheckPath  = $HealthPath
    cpu              = $Cpu
    memory           = $Memory
    cpuArchitecture  = 'X86_64'
    scalingTarget    = @{ minTaskCount = $MinTasks; maxTaskCount = $MaxTasks; autoScalingMetric = 'AVERAGE_CPU'; autoScalingTargetValue = 60 }
    networkConfiguration = @{ subnets = $PublicSubnets }
}

if (Get-ExpressService) {
    Step "Actualizando $Service (despliegue canario)"
    $request = $common + @{ serviceArn = (Get-ServiceArn) }
    Aws ecs update-express-gateway-service --cli-input-json (JsonArg $request) | Out-Null
} else {
    Step "Creando $Service"
    $request = $common + @{
        serviceName           = $Service
        cluster               = $Cluster
        infrastructureRoleArn = (& $roleArn $InfraRole)
        tags                  = @(@{ key = $Tag.Key; value = $Tag.Value })
    }
    Aws ecs create-express-gateway-service --cli-input-json (JsonArg $request) | Out-Null
}
Remove-TempFiles

Step 'Esperando a que el servicio quede estable'
$stable = $false
for ($i = 0; $i -lt 3 -and -not $stable; $i++) {   # services-stable waits up to 10 minutes each time
    $r = Invoke-AwsCli -Arguments @('ecs', 'wait', 'services-stable', '--cluster', $Cluster, '--services', $Service)
    $stable = ($r.Code -eq 0)
}
if (-not $stable) { throw 'El servicio no quedó estable en 30 minutos: mirá logs.ps1 y los eventos del servicio.' }
$ecs = Get-EcsService
Done ("Estable: {0} tarea(s), {1}" -f $ecs.runningCount, $ecs.taskDefinition)

Step 'La base acepta 5432 sólo desde el security group del servicio'
$dbSg = Get-SecurityGroupId $DbSecurityGroup
$serviceSgs = @($ecs.networkConfiguration.awsvpcConfiguration.securityGroups)
if (-not $serviceSgs.Count) { throw 'El servicio no tiene security groups: no debería pasar con Express Mode.' }
$current = @(Aws ec2 describe-security-groups --group-ids $dbSg --query 'SecurityGroups[0].IpPermissions[].UserIdGroupPairs[].GroupId')
foreach ($sg in $serviceSgs) {
    if ($current -contains $sg) { Done "Ya está la regla desde $sg"; continue }
    Aws ec2 authorize-security-group-ingress --group-id $dbSg --protocol tcp --port 5432 --source-group $sg | Out-Null
    Done "5432 desde $sg"
}

$url = Get-ServiceUrl
Done "API: $url"
