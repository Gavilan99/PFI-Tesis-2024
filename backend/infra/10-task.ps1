# Step 10 — One-off tasks inside the VPC, with the service's own image and task definition.
#
#     powershell -File backend\infra\10-task.ps1 -Job migrate         # alembic upgrade head
#     powershell -File backend\infra\10-task.ps1 -Job migrate -ImageTag v1.0.1-models-<hash>   # before 09
#     powershell -File backend\infra\10-task.ps1 -Job bank-dry-run    # import_question_bank.py --version 1 --dry-run
#     powershell -File backend\infra\10-task.ps1 -Job bank-load       # import_question_bank.py --version 1 --activate
#     powershell -File backend\infra\10-task.ps1 -Job grant-subscription -Email persona@ejemplo.com -Days 30
#
# grant-subscription: scripts/grant_subscription.py, a MANUAL paid tier with no payment behind it, for
# the accounts of the user tests until Feature 6 (Mercado Pago) exists. The email goes in the task's
# command override (visible in ECS and CloudTrail); the script's output names only the users.id.
#
# -ImageTag (migrate only): runs the migrations of an image the service is not running yet, so they
# are in the database before the new code that uses them (deploy-runbook.md). It registers a separate,
# one-off task definition (family nureon-api-oneoff): the service's own, with that image and nothing
# else changed, runs it, and deregisters it. The service is not touched. The service's environment is
# the old code's, which is why the migrations read only the database URL (migrations/env.py).
# A migration run this way must work with the code still deployed: add, don't drop or rename.
#
# Never at app start: each is an explicit step. The bank CSV is the one inside the image.
# There is no job for seed_filler_bank.py: version 0 is never loaded in production, and the script is
# not even in the image.
# Order on a new database: migrate -> bank-dry-run -> bank-load, before anyone (the smoke test
# included) creates an attempt: one response freezes a version.
# The task runs with the service's security group (the only one the database accepts) in a public
# subnet with a public IP (no NAT), waits until it stops, prints its log, and fails if it exited non-zero.
# Cost: Fargate by the second, 1 minute minimum: under US$0.01 per run.

param(
    [Parameter(Mandatory = $true)][ValidateSet('migrate', 'bank-dry-run', 'bank-load', 'grant-subscription')][string]$Job,
    [int]$BankVersion = 1,
    [string]$Email,
    [int]$Days = 0,
    [string]$ImageTag
)

. "$PSScriptRoot\_common.ps1"

if ($Job -eq 'grant-subscription') {
    if (-not $Email -or $Days -lt 1) { throw 'grant-subscription necesita -Email y -Days (1 a 366).' }
    Write-Host 'ALTA MANUAL DE SUSCRIPCIÓN, SIN PAGO ASOCIADO.' -ForegroundColor Yellow
}

$commands = @{
    'migrate'      = @('alembic', 'upgrade', 'head')
    'bank-dry-run' = @('python', 'scripts/import_question_bank.py', '--csv', $BankCsvInImage, '--version', [string]$BankVersion, '--dry-run')
    'bank-load'    = @('python', 'scripts/import_question_bank.py', '--csv', $BankCsvInImage, '--version', [string]$BankVersion, '--activate')
    'grant-subscription' = @('python', 'scripts/grant_subscription.py', '--email', [string]$Email, '--days', [string]$Days)
}

if ($ImageTag -and $Job -ne 'migrate') { throw '-ImageTag es sólo para -Job migrate.' }

$ecs = Get-EcsService
if (-not $ecs) {
    throw 'No existe el servicio: corré 09-service.ps1 (la tarea usa su task definition). En un entorno nuevo el orden es el de la primera vez: 09-service y después migrate, sin -ImageTag.'
}
$network = $ecs.networkConfiguration.awsvpcConfiguration
$taskDefinition = $ecs.taskDefinition
$oneOff = $null

if ($ImageTag) {
    Step "Task definition de un solo uso con $Repository`:$ImageTag"
    if (-not (AwsTry ecr describe-images --repository-name $Repository --image-ids "imageTag=$ImageTag")) {
        throw "No está la imagen ${Repository}:$ImageTag en ECR: corré 08-image.ps1."
    }
    $current = Aws ecs describe-task-definition --task-definition $ecs.taskDefinition --query 'taskDefinition'
    $containers = @($current.containerDefinitions)
    if (@($containers | Where-Object { $_.name -eq 'Main' }).Count -ne 1) { throw 'La task definition del servicio no tiene un contenedor Main.' }
    foreach ($container in $containers) {
        if ($container.name -eq 'Main') { $container.image = "$Registry/${Repository}:$ImageTag" }
    }
    # The service's task definition as is, except for the family and the image.
    $registration = @{
        family                  = "$Service-oneoff"
        taskRoleArn             = $current.taskRoleArn
        executionRoleArn        = $current.executionRoleArn
        networkMode             = $current.networkMode
        requiresCompatibilities = @($current.requiresCompatibilities)
        cpu                     = $current.cpu
        memory                  = $current.memory
        containerDefinitions    = $containers
    }
    if ($current.runtimePlatform) { $registration.runtimePlatform = $current.runtimePlatform }
    $oneOff = Aws ecs register-task-definition --cli-input-json (JsonArg $registration) --query 'taskDefinition.taskDefinitionArn'
    Remove-TempFiles
    $taskDefinition = $oneOff
    Done "$oneOff (el servicio sigue con $($ecs.taskDefinition))"
}

Step "Tarea $Job"
Done ($commands[$Job] -join ' ')
$request = @{
    cluster              = $Cluster
    taskDefinition       = $taskDefinition
    launchType           = 'FARGATE'
    count                = 1
    startedBy            = "nureon-$Job"
    networkConfiguration = @{ awsvpcConfiguration = @{ subnets = @($network.subnets); securityGroups = @($network.securityGroups); assignPublicIp = 'ENABLED' } }
    overrides            = @{ containerOverrides = @(@{ name = 'Main'; command = $commands[$Job] }) }
}
try {
    $run = Aws ecs run-task --cli-input-json (JsonArg $request)
    Remove-TempFiles
    if (@($run.failures).Count) { throw "No arrancó: $($run.failures | ConvertTo-Json -Compress)" }
    $taskArn = $run.tasks[0].taskArn
    $taskId = $taskArn.Split('/')[-1]
    Done "Tarea $taskId; esperando a que termine..."

    Aws ecs wait tasks-stopped --cluster $Cluster --tasks $taskArn | Out-Null
    $task = Aws ecs describe-tasks --cluster $Cluster --tasks $taskArn --query 'tasks[0]'
    $main = @($task.containers | Where-Object { $_.name -eq 'Main' })[0]
} finally {
    # A stopped task keeps its record: deregistering only stops the revision from being run again.
    if ($oneOff) { Aws ecs deregister-task-definition --task-definition $oneOff | Out-Null; Done "Desregistrada $oneOff" }
}

Step 'Salida'
$stream = "api/Main/$taskId"
$events = AwsTry logs get-log-events --log-group-name $LogGroup --log-stream-name $stream --start-from-head --query 'events[].message'
if ($events) { $events | ForEach-Object { Write-Host "   $_" } } else { Write-Host "   (sin log en $LogGroup / $stream)" }

if ($main.exitCode -ne 0) { throw "La tarea terminó con código $($main.exitCode): $($task.stoppedReason)" }
Done "Terminó bien (código 0)"
