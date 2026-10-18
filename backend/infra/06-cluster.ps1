# Step 6 — ECS cluster on Fargate and the service's log group.
#
#     powershell -File backend\infra\06-cluster.ps1
#
# The log group is created here, with 30 days of retention, so Express Mode does not make its own and
# the execution role can be scoped to exactly this one. One-off tasks (step 10) log here too.
# Cost: the cluster is free; logs US$0.50 per GB ingested + US$0.03 per GB-month stored (cents).

. "$PSScriptRoot\_common.ps1"

$RetentionDays = 30

Step "Cluster $Cluster"
$c = AwsTry ecs describe-clusters --clusters $Cluster --query 'clusters[0].status'
if ($c -ne 'ACTIVE') {
    Aws ecs create-cluster --cluster-name $Cluster --capacity-providers FARGATE `
        --settings name=containerInsights,value=disabled --tags "key=$($Tag.Key),value=$($Tag.Value)" | Out-Null
    Done 'Creado'
} else { Done 'Ya existe' }

Step "Log group $LogGroup ($RetentionDays días)"
$existing = Aws logs describe-log-groups --log-group-name-prefix $LogGroup --query 'logGroups[].logGroupName'
if (@($existing) -notcontains $LogGroup) {
    Aws logs create-log-group --log-group-name $LogGroup --tags "$($Tag.Key)=$($Tag.Value)" | Out-Null
    Done 'Creado'
} else { Done 'Ya existe' }
Aws logs put-retention-policy --log-group-name $LogGroup --retention-in-days $RetentionDays | Out-Null
Done 'Retención aplicada'
