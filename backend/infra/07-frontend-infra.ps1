# Step 7 — Frontend hosting: private S3 bucket + CloudFront with Origin Access Control.
#
#     powershell -File backend\infra\07-frontend-infra.ps1
#
# Runs before the service: the API's CORS_ALLOWED_ORIGINS is this distribution's domain.
#
# The bucket blocks all public access; only this distribution reads it (OAC, SigV4, bucket policy on
# the distribution's ARN). `index.html` is the root object. Angular's routes: the build prerenders
# most pages, and step 11 uploads each one also at its path without a trailing slash (`/contacto`).
# Anything else (S3 answers 403 without ListBucket) gets `/index.csr.html` with 200: the unrendered app
# shell, so the client renders the route. Not `/index.html`: that is the prerendered home page, and
# hydrating it over another route would not match.
# Cost: S3 cents; CloudFront within the always-free tier (1 TB and 10M requests a month).

. "$PSScriptRoot\_common.ps1"

$CachingOptimized    = '658327ea-f89d-4fab-a63d-7e88639e58f6'   # AWS managed cache policy
$SecurityHeaders     = '67f7725c-6f97-4210-82d7-5512b31e9d03'   # AWS managed response headers policy
$AppShell            = '/index.csr.html'
$OriginId            = 's3-frontend'

Step "Bucket $FrontendBucket (privado)"
if (-not (AwsTry s3api head-bucket --bucket $FrontendBucket)) {
    Aws s3api create-bucket --bucket $FrontendBucket --create-bucket-configuration "LocationConstraint=$Region" | Out-Null
    Done 'Creado'
} else { Done 'Ya existe' }
Aws s3api put-public-access-block --bucket $FrontendBucket `
    --public-access-block-configuration 'BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true' | Out-Null
Aws s3api put-bucket-ownership-controls --bucket $FrontendBucket --ownership-controls 'Rules=[{ObjectOwnership=BucketOwnerEnforced}]' | Out-Null
Aws s3api put-bucket-encryption --bucket $FrontendBucket `
    --server-side-encryption-configuration (JsonArg @{ Rules = @(@{ ApplyServerSideEncryptionByDefault = @{ SSEAlgorithm = 'AES256' } }) }) | Out-Null
Aws s3api put-bucket-tagging --bucket $FrontendBucket --tagging "TagSet=[{Key=$($Tag.Key),Value=$($Tag.Value)}]" | Out-Null
Done 'Acceso público bloqueado, ACLs deshabilitadas, cifrado SSE-S3'

Step "Origin Access Control $FrontendOac"
$oac = @(Aws cloudfront list-origin-access-controls --query 'OriginAccessControlList.Items[]' | Where-Object { $_.Name -eq $FrontendOac })[0]
if (-not $oac) {
    $oacId = Aws cloudfront create-origin-access-control --origin-access-control-config `
        "Name=$FrontendOac,Description=NureonAI frontend bucket,SigningProtocol=sigv4,SigningBehavior=always,OriginAccessControlOriginType=s3" `
        --query 'OriginAccessControl.Id'
    Done "Creado $oacId"
} else { $oacId = $oac.Id; Done "Ya existe $oacId" }

Step 'Distribución de CloudFront'
$dist = Get-Distribution
if (-not $dist) {
    $errorToShell = { param($code) @{ ErrorCode = $code; ResponsePagePath = $AppShell; ResponseCode = '200'; ErrorCachingMinTTL = 10 } }
    $config = @{
        CallerReference   = "nureon-frontend-$([guid]::NewGuid().ToString('N'))"
        Comment           = $DistributionNote
        Enabled           = $true
        DefaultRootObject = 'index.html'
        PriceClass        = 'PriceClass_100'
        HttpVersion       = 'http2and3'
        IsIPV6Enabled     = $true
        Origins           = @{ Quantity = 1; Items = @(@{
                    Id                    = $OriginId
                    DomainName            = "$FrontendBucket.s3.$Region.amazonaws.com"
                    OriginAccessControlId = $oacId
                    S3OriginConfig        = @{ OriginAccessIdentity = '' }
                }) }
        DefaultCacheBehavior = @{
            TargetOriginId          = $OriginId
            ViewerProtocolPolicy    = 'redirect-to-https'
            AllowedMethods          = @{ Quantity = 2; Items = @('GET', 'HEAD'); CachedMethods = @{ Quantity = 2; Items = @('GET', 'HEAD') } }
            Compress                = $true
            CachePolicyId           = $CachingOptimized
            ResponseHeadersPolicyId = $SecurityHeaders
        }
        CustomErrorResponses = @{ Quantity = 2; Items = @((& $errorToShell 403), (& $errorToShell 404)) }
        ViewerCertificate    = @{ CloudFrontDefaultCertificate = $true }
    }
    $request = @{ DistributionConfig = $config; Tags = @{ Items = @(@{ Key = $Tag.Key; Value = $Tag.Value }) } }
    Aws cloudfront create-distribution-with-tags --distribution-config-with-tags (JsonArg $request) | Out-Null
    $dist = Get-Distribution
    Done "Creada $($dist.Id); se despliega en ~5 minutos"
} else { Done "Ya existe $($dist.Id) ($($dist.Status))" }

Step 'Política del bucket: sólo esta distribución lee'
$policy = @{ Version = '2012-10-17'; Statement = @(@{
            Sid       = 'CloudFrontOnly'
            Effect    = 'Allow'
            Principal = @{ Service = 'cloudfront.amazonaws.com' }
            Action    = 's3:GetObject'
            Resource  = "arn:aws:s3:::$FrontendBucket/*"
            Condition = @{ StringEquals = @{ 'AWS:SourceArn' = $dist.Arn } }
        }) }
Aws s3api put-bucket-policy --bucket $FrontendBucket --policy (JsonArg $policy) | Out-Null
Remove-TempFiles
Done 'Aplicada'
Done "Frontend: https://$($dist.Domain)"
