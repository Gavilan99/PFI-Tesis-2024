# Step 5 — The three IAM roles of the service. Run after 02 and 03: the execution role names the secrets.
#
#     powershell -File backend\infra\05-roles.ps1
#
#   nureon-ecs-execution      ECS agent: pull this image, write this log group, read these two secrets.
#   nureon-ecs-task           The app: the Cognito admin calls it makes on this pool, and SES send from
#                             this identity. Nothing else.
#   nureon-ecs-infrastructure Express Mode: ALB, target groups, security groups, certificate, scaling
#                             (AWS managed policy AmazonECSInfrastructureRoleforExpressGatewayServices).
#
# Inline policies are rewritten on every run, so the roles always match this file. The SES identity
# (the contact inbox) is read from backend/.env: it never goes into the repository.
# Cost: US$0.

. "$PSScriptRoot\_common.ps1"

$db = Get-DbInstance
if (-not $db) { throw 'No existe la base: corré 02-database.ps1.' }
$dbSecretArn = $db.MasterUserSecret.SecretArn
$appSecretArn = Get-AppSecretArn
if (-not $appSecretArn) { throw "No existe $AppSecretName`: corré 03-app-secret.ps1." }
$contactInbox = Get-DotEnv 'CONTACT_MAIL_TO'

function Set-Role([string]$Name, [string]$Principal, $TrustCondition, [string]$Description) {
    $statement = @{ Effect = 'Allow'; Principal = @{ Service = $Principal }; Action = 'sts:AssumeRole' }
    if ($TrustCondition) { $statement.Condition = $TrustCondition }
    $trust = @{ Version = '2012-10-17'; Statement = @($statement) }
    if (AwsTry iam get-role --role-name $Name) {
        Aws iam update-assume-role-policy --role-name $Name --policy-document (JsonArg $trust) | Out-Null
        Done "$Name ya existe (confianza actualizada)"
    } else {
        Aws iam create-role --role-name $Name --description $Description --assume-role-policy-document (JsonArg $trust) `
            --tags "Key=$($Tag.Key),Value=$($Tag.Value)" | Out-Null
        Done "$Name creado"
    }
}

function Set-InlinePolicy([string]$Role, [string]$PolicyName, [object[]]$Statements) {
    $doc = @{ Version = '2012-10-17'; Statement = $Statements }
    Aws iam put-role-policy --role-name $Role --policy-name $PolicyName --policy-document (JsonArg $doc) | Out-Null
    Done "  política $PolicyName aplicada"
}

$fromThisAccount = @{ StringEquals = @{ 'aws:SourceAccount' = $AccountId } }

Step "Rol de ejecución $ExecutionRole"
Set-Role $ExecutionRole 'ecs-tasks.amazonaws.com' $null 'NureonAI API: ECS agent (image, logs, secrets)'
Set-InlinePolicy $ExecutionRole 'nureon-execution' @(
    @{ Sid = 'EcrLogin'; Effect = 'Allow'; Action = 'ecr:GetAuthorizationToken'; Resource = '*' },
    @{ Sid = 'PullThisImage'; Effect = 'Allow'
       Action = @('ecr:BatchCheckLayerAvailability', 'ecr:GetDownloadUrlForLayer', 'ecr:BatchGetImage')
       Resource = "arn:aws:ecr:${Region}:${AccountId}:repository/$Repository" },
    @{ Sid = 'WriteThisLogGroup'; Effect = 'Allow'; Action = @('logs:CreateLogStream', 'logs:PutLogEvents')
       Resource = "arn:aws:logs:${Region}:${AccountId}:log-group:${LogGroup}:*" },
    @{ Sid = 'ReadTheTwoSecrets'; Effect = 'Allow'; Action = 'secretsmanager:GetSecretValue'
       Resource = @($dbSecretArn, $appSecretArn) }
)

Step "Rol de la tarea $TaskRole"
Set-Role $TaskRole 'ecs-tasks.amazonaws.com' $fromThisAccount 'NureonAI API: what the app itself calls (Cognito, SES)'
Set-InlinePolicy $TaskRole 'nureon-app' @(
    @{ Sid = 'CognitoAdminOnThisPool'; Effect = 'Allow'
       Action = @('cognito-idp:AdminCreateUser', 'cognito-idp:AdminSetUserPassword', 'cognito-idp:AdminInitiateAuth',
                  'cognito-idp:AdminGetUser', 'cognito-idp:AdminDeleteUser')
       Resource = "arn:aws:cognito-idp:${Region}:${AccountId}:userpool/$UserPoolId" },
    @{ Sid = 'ContactMailFromThisIdentity'; Effect = 'Allow'; Action = @('ses:SendEmail', 'ses:SendRawEmail')
       Resource = "arn:aws:ses:${Region}:${AccountId}:identity/$contactInbox" },
    @{ Sid = 'GenerateResultDescriptions'; Effect = 'Allow'; Action = 'bedrock:InvokeModel'
       Resource = "arn:aws:bedrock:${Region}::foundation-model/$BedrockModelId" }
)

Step "Rol de infraestructura $InfraRole"
Set-Role $InfraRole 'ecs.amazonaws.com' $null 'NureonAI API: Express Mode manages ALB, security groups, certificate, scaling'
Aws iam attach-role-policy --role-name $InfraRole `
    --policy-arn 'arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices' | Out-Null
Done '  política administrada adjunta'
Remove-TempFiles
