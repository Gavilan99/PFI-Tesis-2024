# Step 3 — The app's own secret: SECRET_KEY, generated here and stored only in Secrets Manager.
#
#     powershell -File backend\infra\03-app-secret.ps1
#
# The value is generated locally, goes to AWS through a temp file that is deleted right after, and is
# never printed. Re-running leaves an existing secret alone (it does not rotate the key).
# Cost: US$0.40/month.

. "$PSScriptRoot\_common.ps1"

Step "Secreto $AppSecretName"
$arn = Get-AppSecretArn
if ($arn) { Done "Ya existe $arn"; return }

$bytes = New-Object byte[] 48
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$value = [Convert]::ToBase64String($bytes)
try {
    $arn = Aws secretsmanager create-secret --name $AppSecretName --description 'NureonAI API: SECRET_KEY' `
        --secret-string (JsonArg @{ SECRET_KEY = $value }) --tags "Key=$($Tag.Key),Value=$($Tag.Value)" --query 'ARN'
} finally {
    Remove-TempFiles
    $value = $null
}
Done "Creado $arn"
