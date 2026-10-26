# Step 3 — The app's own secret: SECRET_KEY, generated here, and the two Mercado Pago credentials
# (Feature 6), asked for here. All three stored only in Secrets Manager, as keys of one secret.
#
#     powershell -File backend\infra\03-app-secret.ps1
#
# SECRET_KEY is generated locally. The Mercado Pago access token and webhook secret are the PRODUCTION
# ones (Tus integraciones → tu app → Credenciales de producción, and Webhooks → Configurar
# notificaciones → modo productivo → clave secreta): typed at the prompt, never echoed, never read from
# backend/.env (which holds the test ones). Every value goes to AWS through a temp file that is deleted
# right after, and is never printed.
#
# Re-running adds only the keys that are missing: it never rotates SECRET_KEY nor replaces a Mercado
# Pago credential already stored. To replace one, delete that key in the console and run this again.
# Cost: US$0.40/month (one secret, whatever its keys).

. "$PSScriptRoot\_common.ps1"

$MercadoPagoKeys = [ordered]@{
    MERCADOPAGO_ACCESS_TOKEN   = 'Access Token de producción de Mercado Pago (APP_USR-...)'
    MERCADOPAGO_WEBHOOK_SECRET = 'Clave secreta del webhook de Mercado Pago (modo productivo)'
}

function Read-Secret([string]$Prompt) {
    $secure = Read-Host -Prompt $Prompt -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
    if (-not $value.Trim()) { throw "Vacío: $Prompt." }
    return $value.Trim()
}

Step "Secreto $AppSecretName"
$arn = Get-AppSecretArn
$values = [ordered]@{}
if ($arn) {
    # Only to learn which keys exist and keep them: the values are not printed.
    $current = (Aws secretsmanager get-secret-value --secret-id $AppSecretName --query 'SecretString') | ConvertFrom-Json
    foreach ($property in $current.PSObject.Properties) { $values[$property.Name] = $property.Value }
} else {
    $bytes = New-Object byte[] 48
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $values['SECRET_KEY'] = [Convert]::ToBase64String($bytes)
}

$missing = @($MercadoPagoKeys.Keys | Where-Object { -not $values.Contains($_) })
if ($arn -and $missing.Count -eq 0) {
    $values = $null
    Done "Ya existe $arn, con todas sus claves"
    return
}
foreach ($key in $missing) { $values[$key] = Read-Secret $MercadoPagoKeys[$key] }

try {
    if ($arn) {
        Aws secretsmanager put-secret-value --secret-id $AppSecretName --secret-string (JsonArg $values) | Out-Null
        Done "Agregadas a $arn`: $($missing -join ', ')"
    } else {
        $arn = Aws secretsmanager create-secret --name $AppSecretName `
            --description 'NureonAI API: SECRET_KEY y credenciales de Mercado Pago' `
            --secret-string (JsonArg $values) --tags "Key=$($Tag.Key),Value=$($Tag.Value)" --query 'ARN'
        Done "Creado $arn"
    }
} finally {
    Remove-TempFiles
    $values = $null
}
