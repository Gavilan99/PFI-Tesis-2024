# Step 12 — Smoke test against production, end to end, through the public URLs.
#
#     powershell -File backend\infra\12-smoke.ps1
#     powershell -File backend\infra\12-smoke.ps1 -ApiUrl https://... -Origin https://dxxxx.cloudfront.net
#
# health -> CORS (the frontend's origin allowed, another one not) -> register a test account ->
# create an attempt -> its 40 questions (cut 1) -> answer them all -> the cut status -> complete ->
# result -> delete the account -> the old token is refused.
# Only after 10-task.ps1 bank-load: the attempt is served from the active version and freezes it.
# The account is recognizable (nureon-smoke-<when>@smoke.nureon.invalid, a domain that cannot receive
# mail). Deleting it anonymizes it but keeps its attempt: the printed user id goes in
# docs/deploy-runbook.md, to exclude those rows from any analysis.
# Cost: nothing measurable.

param(
    [string]$ApiUrl,
    [string]$Origin
)

. "$PSScriptRoot\_common.ps1"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

if (-not $ApiUrl) { $ApiUrl = Get-ServiceUrl }
if (-not $Origin) { $Origin = "https://$((Get-Distribution).Domain)" }
if (-not $ApiUrl -or $Origin -eq 'https://') { throw 'Faltan la URL de la API o el dominio del frontend.' }

function Call([string]$Method, [string]$Path, $Body, [string]$Token, [int]$Expect) {
    $headers = @{ Origin = $Origin }
    if ($Token) { $headers.Authorization = "Bearer $Token" }
    $params = @{ Uri = "$ApiUrl$Path"; Method = $Method; Headers = $headers; UseBasicParsing = $true }
    if ($null -ne $Body) {
        $params.Body = [Text.Encoding]::UTF8.GetBytes(($Body | ConvertTo-Json -Depth 10 -Compress))
        $params.ContentType = 'application/json; charset=utf-8'
    }
    try { $resp = Invoke-WebRequest @params; $status = [int]$resp.StatusCode; $content = $resp.Content }
    catch [Net.WebException] {
        if (-not $_.Exception.Response) { throw }
        $status = [int]$_.Exception.Response.StatusCode
        $content = (New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())).ReadToEnd()
    }
    if ($status -ne $Expect) { throw "$Method $Path respondió $status (esperaba $Expect): $content" }
    Done "$Method $Path -> $status"
    # Flask escapes non-ASCII in JSON (é), so the body decodes the same under any charset.
    # Assigned first: in 5.1, ConvertFrom-Json emits a JSON array as one object; `return` then unrolls it.
    if ($content) { $parsed = $content | ConvertFrom-Json; return $parsed }
}

function Preflight([string]$From) {
    $req = [Net.WebRequest]::Create("$ApiUrl/api/auth/register")
    $req.Method = 'OPTIONS'
    $req.Headers.Add('Origin', $From)
    $req.Headers.Add('Access-Control-Request-Method', 'POST')
    $req.Headers.Add('Access-Control-Request-Headers', 'content-type')
    try { $resp = $req.GetResponse() } catch [Net.WebException] { $resp = $_.Exception.Response }
    $allowed = $resp.Headers['Access-Control-Allow-Origin']
    $resp.Close()
    return $allowed
}

Step "Humo contra $ApiUrl (origen $Origin)"
Call GET '/api/health' $null $null 200 | Out-Null

Step 'CORS'
$allowed = Preflight $Origin
if ($allowed -ne $Origin) { throw "El preflight desde $Origin no lo permite (Access-Control-Allow-Origin: '$allowed')." }
Done "permitido desde $Origin"
$foreign = Preflight 'https://not-nureon.example'
if ($foreign) { throw "Un origen ajeno quedó permitido: '$foreign'." }
Done 'un origen ajeno no recibe Access-Control-Allow-Origin'

Step 'Cuenta de prueba'
$when = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$email = "nureon-smoke-$when@smoke.nureon.invalid"
$bytes = New-Object byte[] 24
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$password = 'Smoke-' + [Convert]::ToBase64String($bytes)
$reg = Call POST '/api/auth/register' @{ username = "nureon-smoke-$when"; email = $email; password = $password } $null 201
$password = $null
$token = $reg.accessToken
$userId = $reg.user.id
Done "email $email"

Step 'Intento: corte 1'
$attempt = Call POST '/api/attempts' $null $token 201
$questions = @(Call GET "/api/attempts/$($attempt.id)/questions" $null $token 200)
Done ("{0} preguntas, tier {1}, versión {2}" -f $questions.Count, $attempt.tier, $attempt.questionnaireVersion)
if ($questions.Count -ne 40) { throw "El corte 1 tiene que servir 40 preguntas; sirvió $($questions.Count)." }
foreach ($q in $questions) {
    $body = @{ questionId = $q.id; selectedOptionId = $q.answerOptions[0].id; freeTextResponse = $null; orderingResponse = $null }
    $null = Call POST "/api/attempts/$($attempt.id)/responses" $body $token 200 6>$null
}
Done '40 respuestas'
$cut = Call GET "/api/attempts/$($attempt.id)/cut" $null $token 200
if ($cut.currentCut -ne 1 -or $cut.cutCount -ne 3 -or $cut.servedItems -ne 40 -or $cut.answeredItems -ne 40 -or $cut.nextCutItems -ne 50) {
    throw "Estado del corte inesperado: $($cut | ConvertTo-Json -Compress)"
}
Done ("corte {0} de {1}, precisión estimada {2:P0}; el siguiente agrega {3} ítems ({4:P0}); puede seguir: {5}" -f `
    $cut.currentCut, $cut.cutCount, $cut.currentCutAccuracy, $cut.nextCutItems, $cut.nextCutAccuracy, $cut.canContinue)
$completed = Call POST "/api/attempts/$($attempt.id)/complete" $null $token 200
if ($completed.status -ne 'completed') { throw "El intento quedó en '$($completed.status)'." }
$result = Call GET "/api/attempts/$($attempt.id)/result" $null $token 200
Done "eneatipo $($result.eneatype)"

Step 'Borrado de la cuenta'
Call DELETE '/api/users/me' $null $token 204 | Out-Null
Call GET '/api/attempts/latest' $null $token 401 | Out-Null

Step 'Para el runbook'
Write-Host "   Cuenta de humo: users.id = $userId  ($email, $when UTC), intento $($attempt.id)" -ForegroundColor Yellow
Done 'Humo en verde'
