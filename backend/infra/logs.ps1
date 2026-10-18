# Recent production logs, and a scan for what must never be in them. Read-only.
#
#     powershell -File backend\infra\logs.ps1                 # last 30 minutes
#     powershell -File backend\infra\logs.ps1 -Minutes 120 -Scan
#
# -Scan looks for emails, bearer tokens, JWTs, Authorization headers and password fields in every
# line of the window, and fails if it finds any. The app logs only method, path, status and request id.

param(
    [int]$Minutes = 30,
    [switch]$Scan
)

. "$PSScriptRoot\_common.ps1"

$since = [DateTimeOffset]::UtcNow.AddMinutes(-$Minutes).ToUnixTimeMilliseconds()
$events = @(Aws logs filter-log-events --log-group-name $LogGroup --start-time $since --query 'events[].message')
Step "$($events.Count) líneas de $LogGroup en los últimos $Minutes minutos"
$events | ForEach-Object { Write-Host "   $_" }

if ($Scan) {
    Step 'Búsqueda de datos que no deberían estar'
    $patterns = [ordered]@{
        'email'         = '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
        'bearer token'  = '(?i)bearer\s+[A-Za-z0-9._-]{10,}'
        'JWT'           = 'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.'
        'Authorization' = '(?i)authorization'
        'password'      = '(?i)"?(password|contrase)'
    }
    $found = 0
    foreach ($name in $patterns.Keys) {
        $hits = @($events | Where-Object { $_ -match $patterns[$name] })
        if ($hits.Count) { $found += $hits.Count; Write-Host "   $name`: $($hits.Count) línea(s)" -ForegroundColor Red }
        else { Done "$name`: ninguna" }
    }
    if ($found) { throw "Hay $found línea(s) que no deberían estar en los logs." }
}
