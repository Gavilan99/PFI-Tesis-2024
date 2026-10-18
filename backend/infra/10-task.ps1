# Step 10 — One-off tasks inside the VPC, with the service's own image and task definition.
#
#     powershell -File backend\infra\10-task.ps1 -Job migrate         # alembic upgrade head
#     powershell -File backend\infra\10-task.ps1 -Job bank-dry-run    # import_question_bank.py --version 1 --dry-run
#     powershell -File backend\infra\10-task.ps1 -Job bank-load       # import_question_bank.py --version 1 --activate
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
    [Parameter(Mandatory = $true)][ValidateSet('migrate', 'bank-dry-run', 'bank-load')][string]$Job,
    [int]$BankVersion = 1
)

. "$PSScriptRoot\_common.ps1"

$commands = @{
    'migrate'      = @('alembic', 'upgrade', 'head')
    'bank-dry-run' = @('python', 'scripts/import_question_bank.py', '--csv', $BankCsvInImage, '--version', [string]$BankVersion, '--dry-run')
    'bank-load'    = @('python', 'scripts/import_question_bank.py', '--csv', $BankCsvInImage, '--version', [string]$BankVersion, '--activate')
}

$ecs = Get-EcsService
if (-not $ecs) { throw 'No existe el servicio: corré 09-service.ps1 (la tarea usa su task definition).' }
$network = $ecs.networkConfiguration.awsvpcConfiguration

Step "Tarea $Job"
Done ($commands[$Job] -join ' ')
$request = @{
    cluster              = $Cluster
    taskDefinition       = $ecs.taskDefinition
    launchType           = 'FARGATE'
    count                = 1
    startedBy            = "nureon-$Job"
    networkConfiguration = @{ awsvpcConfiguration = @{ subnets = @($network.subnets); securityGroups = @($network.securityGroups); assignPublicIp = 'ENABLED' } }
    overrides            = @{ containerOverrides = @(@{ name = 'Main'; command = $commands[$Job] }) }
}
$run = Aws ecs run-task --cli-input-json (JsonArg $request)
Remove-TempFiles
if (@($run.failures).Count) { throw "No arrancó: $($run.failures | ConvertTo-Json -Compress)" }
$taskArn = $run.tasks[0].taskArn
$taskId = $taskArn.Split('/')[-1]
Done "Tarea $taskId; esperando a que termine..."

Aws ecs wait tasks-stopped --cluster $Cluster --tasks $taskArn | Out-Null
$task = Aws ecs describe-tasks --cluster $Cluster --tasks $taskArn --query 'tasks[0]'
$main = @($task.containers | Where-Object { $_.name -eq 'Main' })[0]

Step 'Salida'
$stream = "api/Main/$taskId"
$events = AwsTry logs get-log-events --log-group-name $LogGroup --log-stream-name $stream --start-from-head --query 'events[].message'
if ($events) { $events | ForEach-Object { Write-Host "   $_" } } else { Write-Host "   (sin log en $LogGroup / $stream)" }

if ($main.exitCode -ne 0) { throw "La tarea terminó con código $($main.exitCode): $($task.stoppedReason)" }
Done "Terminó bien (código 0)"
