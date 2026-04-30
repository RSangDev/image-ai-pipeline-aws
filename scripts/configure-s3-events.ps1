# Configure S3 Event Notifications (PowerShell)
# Run this if S3 notifications weren't configured during deployment

$ErrorActionPreference = "Stop"

Write-Host "Configuring S3 Event Notifications..." -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""

# Configuration
$ProjectName = "image-ai-pipeline"
$Region = "us-east-2"
$StackName = "$ProjectName-stack"

Write-Host "Getting stack information..." -ForegroundColor Yellow

try {
    # Get bucket name
    $imagesBucket = aws cloudformation describe-stacks `
        --stack-name $StackName `
        --query 'Stacks[0].Outputs[?OutputKey==`ImagesBucketName`].OutputValue' `
        --output text `
        --region $Region 2>&1
    
    # Get processor function name
    $processorFunction = aws cloudformation describe-stacks `
        --stack-name $StackName `
        --query 'Stacks[0].Outputs[?OutputKey==`ProcessorFunctionName`].OutputValue' `
        --output text `
        --region $Region 2>&1
    
    Write-Host "  Bucket: $imagesBucket" -ForegroundColor Gray
    Write-Host "  Function: $processorFunction" -ForegroundColor Gray
    
    # Get Lambda ARN
    $lambdaArn = aws lambda get-function `
        --function-name $processorFunction `
        --query 'Configuration.FunctionArn' `
        --output text `
        --region $Region 2>&1
    
    Write-Host "  Lambda ARN: $lambdaArn" -ForegroundColor Gray
    Write-Host ""
    
    # Create notification configuration
    Write-Host "Creating notification configuration..." -ForegroundColor Yellow
    
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
    
    # Convert to JSON and save temporarily
    $jsonContent = $notificationConfig | ConvertTo-Json -Depth 10
    $tempFile = New-TemporaryFile
    
    # CRITICAL: Save as UTF-8 WITHOUT BOM
    [System.IO.File]::WriteAllText($tempFile.FullName, $jsonContent, [System.Text.UTF8Encoding]::new($false))
    
    Write-Host "Applying S3 notification configuration..." -ForegroundColor Yellow
    
    # Apply configuration
    aws s3api put-bucket-notification-configuration `
        --bucket $imagesBucket `
        --notification-configuration "file://$($tempFile.FullName)" `
        --region $Region
    
    # Cleanup
    Remove-Item $tempFile -ErrorAction SilentlyContinue
    
    Write-Host ""
    Write-Host "=======================================" -ForegroundColor Green
    Write-Host "SUCCESS! S3 Notifications Configured" -ForegroundColor Green
    Write-Host "=======================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Test it:" -ForegroundColor Cyan
    Write-Host "  aws s3 cp test.jpg s3://$imagesBucket/" -ForegroundColor Gray
    Write-Host "  (Lambda will be triggered automatically)" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to configure S3 notifications" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible causes:" -ForegroundColor Yellow
    Write-Host "  1. Stack not deployed yet" -ForegroundColor Gray
    Write-Host "  2. AWS credentials not configured" -ForegroundColor Gray
    Write-Host "  3. Insufficient permissions" -ForegroundColor Gray
    Write-Host ""
    exit 1
}