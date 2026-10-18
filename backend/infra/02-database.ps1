# Step 2 — RDS PostgreSQL 16, private, with its master password managed by Secrets Manager.
#
#     powershell -File backend\infra\02-database.ps1
#
# db.t4g.micro, 20 GB gp3, single zone, encrypted at rest, 7 days of backups, not publicly
# accessible, deletion protection on. RDS creates and owns the master secret (rds!db-...); nobody
# sees the password, and the deploy profile cannot read it.
# The secret's rotation is stretched to 365 days: tasks read it at start, so after a rotation they
# need a new deployment (docs/deploy-runbook.md).
# Cost: ~US$14/month (US$0.016/h + 20 GB x US$0.115). Takes ~10 minutes. Re-runnable.

. "$PSScriptRoot\_common.ps1"

$InstanceClass   = 'db.t4g.micro'
$EngineVersion   = '16.15'
$StorageGb       = 20
$BackupDays      = 7
$RotationDays    = 365

$sg = Get-SecurityGroupId $DbSecurityGroup
if (-not $sg) { throw "No existe el security group ${DbSecurityGroup}: corré 01-network.ps1." }

Step "Instancia $DbInstance"
$db = Get-DbInstance
if (-not $db) {
    Aws rds create-db-instance `
        --db-instance-identifier $DbInstance `
        --engine postgres --engine-version $EngineVersion --auto-minor-version-upgrade `
        --db-instance-class $InstanceClass `
        --storage-type gp3 --allocated-storage $StorageGb --storage-encrypted `
        --db-name $DbName --master-username $DbMasterUser --manage-master-user-password `
        --db-subnet-group-name $DbSubnetGroup --vpc-security-group-ids $sg `
        --no-publicly-accessible --no-multi-az `
        --backup-retention-period $BackupDays --copy-tags-to-snapshot --deletion-protection `
        --monitoring-interval 0 --no-enable-performance-insights `
        --tags "Key=$($Tag.Key),Value=$($Tag.Value)" | Out-Null
    Done 'Creación pedida; esperando a que quede disponible (~10 min)...'
} else { Done "Ya existe ($($db.DBInstanceStatus))" }
Aws rds wait db-instance-available --db-instance-identifier $DbInstance | Out-Null
$db = Get-DbInstance
Done ("Disponible en {0}:{1}; pública: {2}; cifrada: {3}; backups: {4} días" -f $db.Endpoint.Address, $db.Endpoint.Port,
    $db.PubliclyAccessible, $db.StorageEncrypted, $db.BackupRetentionPeriod)
if ($db.PubliclyAccessible) { throw 'La instancia quedó accesible públicamente: no debería.' }

Step "Rotación del secreto maestro cada $RotationDays días"
$secretArn = $db.MasterUserSecret.SecretArn
$current = Aws secretsmanager describe-secret --secret-id $secretArn --query 'RotationRules.AutomaticallyAfterDays'
if ($current -ne $RotationDays) {
    Aws secretsmanager rotate-secret --secret-id $secretArn --rotation-rules "AutomaticallyAfterDays=$RotationDays" --no-rotate-immediately | Out-Null
    Done "Cambiada de $current a $RotationDays días"
} else { Done "Ya está en $RotationDays días" }
Done "Secreto: $secretArn"
