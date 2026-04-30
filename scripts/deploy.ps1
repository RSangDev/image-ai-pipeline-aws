# Image AI Pipeline - Deploy Script (PowerShell)
# Deploys complete CloudFormation stack

$ErrorActionPreference = "Stop"

Write-Host "Image AI Pipeline - Deployment Script" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""

# Configuration
$ProjectName = "image-ai-pipeline"
$Region = "us-east-2"
$StackName = "$ProjectName-stack"

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Project Name: $ProjectName"
Write-Host "  AWS Region: $Region"
Write-Host "  Stack Name: $StackName"
Write-Host ""

# Check AWS CLI
Write-Host "Checking AWS CLI..." -ForegroundColor Yellow
try {
    $awsVersion = aws --version 2>&1
    Write-Host "[OK] AWS CLI installed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] AWS CLI not found" -ForegroundColor Red
    exit 1
}

# Check credentials
Write-Host "Checking AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity 2>&1 | ConvertFrom-Json
    Write-Host "[OK] AWS credentials configured" -ForegroundColor Green
    Write-Host "  Account: $($identity.Account)" -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] AWS credentials not configured" -ForegroundColor Red
    Write-Host "Run: aws configure" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Step 1: Packaging Lambda functions..." -ForegroundColor Yellow

# Package image-processor
Write-Host "  Packaging image-processor..." -ForegroundColor Gray
Set-Location lambda/image-processor
if (Test-Path "function.zip") { Remove-Item "function.zip" }
Compress-Archive -Path handler.py -DestinationPath function.zip -Force
Set-Location ../..

# Package image-search
Write-Host "  Packaging image-search..." -ForegroundColor Gray
Set-Location lambda/image-search
if (Test-Path "function.zip") { Remove-Item "function.zip" }
Compress-Archive -Path handler.py -DestinationPath function.zip -Force
Set-Location ../..

# Package content-moderation
Write-Host "  Packaging content-moderation..." -ForegroundColor Gray
Set-Location lambda/content-moderation
if (Test-Path "function.zip") { Remove-Item "function.zip" }
Compress-Archive -Path handler.py -DestinationPath function.zip -Force
Set-Location ../..

Write-Host "[OK] Lambda functions packaged" -ForegroundColor Green

Write-Host ""
Write-Host "Step 2: Creating deployment bucket..." -ForegroundColor Yellow

$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$bucketName = "$ProjectName-deploy-$timestamp"

try {
    aws s3 mb "s3://$bucketName" --region $Region 2>&1 | Out-Null
    Write-Host "[OK] Deployment bucket created: $bucketName" -ForegroundColor Green
} catch {
    Write-Host "Trying alternative bucket name..." -ForegroundColor Yellow
    $bucketName = "$ProjectName-deploy-alt-$timestamp"
    aws s3 mb "s3://$bucketName" --region $Region 2>&1 | Out-Null
    Write-Host "[OK] Deployment bucket created: $bucketName" -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 3: Packaging CloudFormation template..." -ForegroundColor Yellow

aws cloudformation package `
    --template-file cloudformation/template.yaml `
    --s3-bucket $bucketName `
    --output-template-file packaged-template.yaml `
    --region $Region 2>&1 | Out-Null

Write-Host "[OK] Template packaged" -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Deploying CloudFormation stack..." -ForegroundColor Yellow
Write-Host "  This may take 3-4 minutes..." -ForegroundColor Gray

try {
    aws cloudformation deploy `
        --template-file packaged-template.yaml `
        --stack-name $StackName `
        --capabilities CAPABILITY_IAM `
        --parameter-overrides ProjectName=$ProjectName `
        --region $Region
    
    Write-Host "[OK] Stack deployed successfully" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Stack deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 5: Updating Lambda function codes..." -ForegroundColor Yellow

# Get function names
$outputs = aws cloudformation describe-stacks `
    --stack-name $StackName `
    --region $Region `
    --query 'Stacks[0].Outputs' 2>&1 | ConvertFrom-Json

$processorFunction = ($outputs | Where-Object { $_.OutputKey -eq "ProcessorFunctionName" }).OutputValue
$searchFunction = ($outputs | Where-Object { $_.OutputKey -eq "SearchFunctionName" }).OutputValue

# Update processor function
Write-Host "  Updating image-processor..." -ForegroundColor Gray
aws lambda update-function-code `
    --function-name $processorFunction `
    --zip-file fileb://lambda/image-processor/function.zip `
    --region $Region 2>&1 | Out-Null

# Update search function
Write-Host "  Updating image-search..." -ForegroundColor Gray
aws lambda update-function-code `
    --function-name $searchFunction `
    --zip-file fileb://lambda/image-search/function.zip `
    --region $Region 2>&1 | Out-Null

Write-Host "[OK] Lambda functions updated" -ForegroundColor Green

Write-Host ""
Write-Host "Step 6: Configuring S3 event notifications..." -ForegroundColor Yellow

try {
    # Debug: Show all outputs
    Write-Host "  DEBUG: Available outputs:" -ForegroundColor DarkGray
    $outputs | ForEach-Object { Write-Host "    - $($_.OutputKey) = $($_.OutputValue)" -ForegroundColor DarkGray }
    
    # Get bucket name from stack outputs
    $imagesBucket = ($outputs | Where-Object { $_.OutputKey -eq "ImagesBucketName" }).OutputValue
    
    if (-not $imagesBucket) {
        Write-Host "  ERROR: Bucket name not found in outputs!" -ForegroundColor Red
        throw "Bucket name not found in stack outputs"
    }
    
    # Get Lambda ARN
    $lambdaArn = aws lambda get-function `
        --function-name $processorFunction `
        --query 'Configuration.FunctionArn' `
        --output text `
        --region $Region 2>&1
    
    if (-not $lambdaArn -or $lambdaArn -like "*error*") {
        throw "Failed to get Lambda ARN"
    }
    
    Write-Host "  Bucket: $imagesBucket" -ForegroundColor Gray
    Write-Host "  Lambda ARN: $lambdaArn" -ForegroundColor Gray
    
    # Create notification configuration JSON
    $notificationConfig = @{
        LambdaFunctionConfigurations = @(
            @{
                Id = "ImageProcessorJPG"
                LambdaFunctionArn = $lambdaArn
                Events = @("s3:ObjectCreated:*")
                Filter = @{
                    Key = @{
                        FilterRules = @(
                            @{
                                Name = "suffix"
                                Value = ".jpg"
                            }
                        )
                    }
                }
            },
            @{
                Id = "ImageProcessorJPEG"
                LambdaFunctionArn = $lambdaArn
                Events = @("s3:ObjectCreated:*")
                Filter = @{
                    Key = @{
                        FilterRules = @(
                            @{
                                Name = "suffix"
                                Value = ".jpeg"
                            }
                        )
                    }
                }
            },
            @{
                Id = "ImageProcessorPNG"
                LambdaFunctionArn = $lambdaArn
                Events = @("s3:ObjectCreated:*")
                Filter = @{
                    Key = @{
                        FilterRules = @(
                            @{
                                Name = "suffix"
                                Value = ".png"
                            }
                        )
                    }
                }
            }
        )
    }
    
    # Convert to JSON and save
    $jsonContent = $notificationConfig | ConvertTo-Json -Depth 10
    $tempFile = New-TemporaryFile
    
    # CRITICAL: Save as UTF-8 WITHOUT BOM
    [System.IO.File]::WriteAllText($tempFile.FullName, $jsonContent, [System.Text.UTF8Encoding]::new($false))
    
    # Apply configuration
    Write-Host "  Applying notification configuration..." -ForegroundColor Gray
    aws s3api put-bucket-notification-configuration `
        --bucket $imagesBucket `
        --notification-configuration "file://$($tempFile.FullName)" `
        --region $Region
    
    # Cleanup
    Remove-Item $tempFile.FullName -ErrorAction SilentlyContinue
    
    Write-Host "[OK] S3 event notifications configured" -ForegroundColor Green
    
} catch {
    Write-Host "[WARNING] Failed to configure S3 notifications" -ForegroundColor Yellow
    Write-Host "  Error: $_" -ForegroundColor Gray
    Write-Host "  You can configure manually later with:" -ForegroundColor Gray
    Write-Host "  .\scripts\configure-s3-events.ps1" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Step 7: Retrieving outputs..." -ForegroundColor Yellow

$apiEndpoint = ($outputs | Where-Object { $_.OutputKey -eq "ApiEndpoint" }).OutputValue
$imagesBucket = ($outputs | Where-Object { $_.OutputKey -eq "ImagesBucketName" }).OutputValue
$uploadCommand = ($outputs | Where-Object { $_.OutputKey -eq "UploadCommand" }).OutputValue

Write-Host ""
Write-Host "=======================================" -ForegroundColor Green
Write-Host "DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Stack Outputs:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  API Endpoint:" -ForegroundColor White
Write-Host "    $apiEndpoint" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Images S3 Bucket:" -ForegroundColor White
Write-Host "    $imagesBucket" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Processor Function:" -ForegroundColor White
Write-Host "    $processorFunction" -ForegroundColor Gray
Write-Host ""
Write-Host "  Search Function:" -ForegroundColor White
Write-Host "    $searchFunction" -ForegroundColor Gray
Write-Host ""
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Upload test images:" -ForegroundColor White
Write-Host "   $uploadCommand" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Run dashboard:" -ForegroundColor White
Write-Host "   cd dashboard" -ForegroundColor Gray
Write-Host "   pip install -r requirements.txt" -ForegroundColor Gray
Write-Host "   streamlit run app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Configure dashboard:" -ForegroundColor White
Write-Host "   API Endpoint: $apiEndpoint" -ForegroundColor Yellow
Write-Host "   S3 Bucket: $imagesBucket" -ForegroundColor Yellow
Write-Host ""
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""

# Save deployment info
$deploymentInfo = @"
Image AI Pipeline - Deployment Info
====================================

Deployed: $(Get-Date)
Stack Name: $StackName
AWS Region: $Region

API Endpoint: $apiEndpoint
Images Bucket: $imagesBucket
Processor Function: $processorFunction
Search Function: $searchFunction

Upload Command:
$uploadCommand

Dashboard Config:
- API Endpoint: $apiEndpoint
- S3 Bucket: $imagesBucket

Rekognition Info:
- Free Tier: 5,000 images/month
- After: `$0.001 per image
- Features: Labels, Faces, Text, Moderation, Celebrities
"@

$deploymentInfo | Out-File -FilePath deployment-info.txt -Encoding UTF8
Write-Host "[OK] Deployment info saved to: deployment-info.txt" -ForegroundColor Green
Write-Host ""