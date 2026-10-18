# What exists right now, with its monthly cost. Read-only.
#
#     powershell -File backend\infra\status.ps1
#
# Costs are on-demand list prices in us-east-2 (Pricing API, 2026-10-18), 730 hours a month.

. "$PSScriptRoot\_common.ps1"

$rows = New-Object System.Collections.ArrayList
function Row([string]$What, [string]$State, [double]$Usd) { [void]$rows.Add([pscustomobject]@{ Recurso = $What; Estado = $State; 'US$/mes' = $Usd }) }

$sg = Get-SecurityGroupId $DbSecurityGroup
$subnets = @(Aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VpcId" 'Name=tag:Project,Values=nureon' --query 'Subnets[].SubnetId')
Row 'Subnets privadas + tabla de rutas + DB subnet group' ("{0} subnets" -f $subnets.Count) 0
Row "Security group $DbSecurityGroup" ($(if ($sg) { $sg } else { '—' })) 0

$db = Get-DbInstance
if ($db) { Row "RDS $DbInstance ($($db.DBInstanceClass), $($db.AllocatedStorage) GB)" $db.DBInstanceStatus ([math]::Round(0.016 * 730 + 0.115 * $db.AllocatedStorage, 2)) }
else { Row "RDS $DbInstance" '—' 0 }

$secrets = @(Aws secretsmanager list-secrets --query 'SecretList[].Name' | Where-Object { $_ -eq $AppSecretName -or $_ -like 'rds!db-*' })
Row 'Secrets Manager (RDS + app)' ("{0} secretos" -f $secrets.Count) (0.40 * $secrets.Count)

$images = AwsTry ecr describe-images --repository-name $Repository --query 'length(imageDetails)'
if ($null -ne $images) { Row "ECR $Repository" "$images imágenes" 0.3 } else { Row "ECR $Repository" '—' 0 }

$svc = Get-ExpressService
if ($svc) {
    $ecs = Get-EcsService
    $tasks = [int]$ecs.runningCount
    Row "Express Mode $Service (Fargate 0,5 vCPU / 1 GB)" ("{0}, {1} tarea(s)" -f $svc.status.statusCode, $tasks) ([math]::Round(0.024685 * 730 * [math]::Max($tasks, 1), 2))
    Row 'ALB de Express Mode' (Get-ServiceUrl) ([math]::Round(0.0225 * 730 + 0.008 * 730 * 0.1, 2))
    Row 'IPv4 públicas (2 ALB + tareas)' ("{0}" -f (2 + $tasks)) ([math]::Round(0.005 * 730 * (2 + $tasks), 2))
} else { Row "Express Mode $Service" '—' 0 }

$lg = Aws logs describe-log-groups --log-group-name-prefix $LogGroup --query 'logGroups[0].storedBytes'
if ($null -ne $lg) { Row "Logs $LogGroup" ("{0:N1} MB" -f ($lg / 1MB)) 0.5 } else { Row "Logs $LogGroup" '—' 0 }

$dist = Get-Distribution
Row 'CloudFront + S3 del frontend' ($(if ($dist) { "https://$($dist.Domain) ($($dist.Status))" } else { '—' })) 0

$rows | Format-Table -AutoSize -Wrap
$total = ($rows | Measure-Object -Property 'US$/mes' -Sum).Sum
Write-Host ("Total estimado: US$ {0:N2} por mes" -f $total) -ForegroundColor Yellow
$plan = Aws freetier get-account-plan-state
Write-Host ("Plan {0}: quedan US$ {1} de crédito" -f $plan.accountPlanType, $plan.accountPlanRemainingCredits.amount)
