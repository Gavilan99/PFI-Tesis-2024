# Step 1 — Private network for the database, inside the default VPC.
#
#     powershell -File backend\infra\01-network.ps1
#
# Creates: two private subnets (two zones), a route table with no internet gateway (only the VPC's
# local route), the DB subnet group, and the database security group with no ingress yet (step 9
# opens 5432 to the service's security group, once Express Mode has created it).
# Cost: US$0. Re-runnable: what already exists is left as is.

. "$PSScriptRoot\_common.ps1"

$PrivateSubnets = [ordered]@{   # name -> zone, CIDR. Outside the default subnets (172.31.0.0/20, 16.0/20, 32.0/20).
    'nureon-private-a' = @("${Region}a", '172.31.48.0/24')
    'nureon-private-b' = @("${Region}b", '172.31.49.0/24')
}

function TagSpec([string]$Type, [string]$Name) {
    return "ResourceType=$Type,Tags=[{Key=Name,Value=$Name},{Key=$($Tag.Key),Value=$($Tag.Value)}]"
}

Step 'Tabla de rutas privada (sin internet gateway)'
$rt = Aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VpcId" "Name=tag:Name,Values=$PrivateRouteTable" --query 'RouteTables[0].RouteTableId'
if (-not $rt) {
    $rt = Aws ec2 create-route-table --vpc-id $VpcId --tag-specifications (TagSpec 'route-table' $PrivateRouteTable) --query 'RouteTable.RouteTableId'
    Done "Creada $rt"
} else { Done "Ya existe $rt" }
$routes = Aws ec2 describe-route-tables --route-table-ids $rt --query 'RouteTables[0].Routes[].GatewayId'
if (@($routes | Where-Object { $_ -ne 'local' }).Count) { throw "La tabla $rt tiene rutas además de la local: $($routes -join ', ')" }

Step 'Subnets privadas'
$subnetIds = @()
foreach ($name in $PrivateSubnets.Keys) {
    $zone, $cidr = $PrivateSubnets[$name]
    $id = Aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VpcId" "Name=tag:Name,Values=$name" --query 'Subnets[0].SubnetId'
    if (-not $id) {
        $id = Aws ec2 create-subnet --vpc-id $VpcId --availability-zone $zone --cidr-block $cidr --tag-specifications (TagSpec 'subnet' $name) --query 'Subnet.SubnetId'
        Done "Creada $name $id ($zone, $cidr)"
    } else { Done "Ya existe $name $id" }
    # No public IPs on launch, and the private table instead of the VPC's main one (which has the IGW).
    Aws ec2 modify-subnet-attribute --subnet-id $id --no-map-public-ip-on-launch | Out-Null
    $assoc = Aws ec2 describe-route-tables --filters "Name=association.subnet-id,Values=$id" --query 'RouteTables[0].RouteTableId'
    if ($assoc -ne $rt) { Aws ec2 associate-route-table --route-table-id $rt --subnet-id $id | Out-Null; Done "  asociada a $rt" }
    $subnetIds += $id
}

Step 'DB subnet group'
if (-not (AwsTry rds describe-db-subnet-groups --db-subnet-group-name $DbSubnetGroup)) {
    Aws rds create-db-subnet-group --db-subnet-group-name $DbSubnetGroup --db-subnet-group-description 'NureonAI database, private subnets' `
        --subnet-ids @subnetIds --tags "Key=$($Tag.Key),Value=$($Tag.Value)" | Out-Null
    Done "Creado $DbSubnetGroup"
} else { Done "Ya existe $DbSubnetGroup" }

Step 'Security group de la base (sin reglas de entrada todavía)'
$sg = Get-SecurityGroupId $DbSecurityGroup
if (-not $sg) {
    $sg = Aws ec2 create-security-group --group-name $DbSecurityGroup --description 'NureonAI database: 5432 only from the API service' `
        --vpc-id $VpcId --tag-specifications (TagSpec 'security-group' $DbSecurityGroup) --query 'GroupId'
    Done "Creado $sg"
} else { Done "Ya existe $sg" }
# A database never starts connections: drop the default allow-all egress.
$egress = Aws ec2 describe-security-groups --group-ids $sg --query 'SecurityGroups[0].IpPermissionsEgress'
if (@($egress).Count) {
    Aws ec2 revoke-security-group-egress --group-id $sg --ip-permissions (JsonArg @($egress)) | Out-Null
    Done '  salida por defecto quitada'
}
Remove-TempFiles
