# CI/CD Setup for Lambda Deployment

## Overview

This repo deploys the two existing Lambdas as **container images**:

- `rearc-sync-and-fetch` (scheduled daily)
- `rearc-analytics` (triggered from SQS)

Terraform creates the infrastructure (including ECR repositories). GitHub Actions builds Docker images, pushes them to ECR, then updates the Lambda functions to the new image URIs.

## Setup

### 1. Configure AWS Credentials in GitHub Secrets

Go to your GitHub repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
- `AWS_REGION` - AWS region (example: `us-east-1`)

**Security Note:** Use a dedicated IAM user with minimal permissions (Lambda update only).

### 2. IAM Policy for CI/CD User

Create an IAM user with this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:UpdateFunctionCode",
        "lambda:PublishVersion",

        "ecr:DescribeRepositories",
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:CompleteLayerUpload",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart"
      ],
      "Resource": [
        "arn:aws:lambda:us-east-1:*:function:rearc-sync-and-fetch",
        "arn:aws:lambda:us-east-1:*:function:rearc-analytics"
      ]
    }
  ]
}
```

### 3. Workflow Triggers

The CI/CD pipeline runs when:
- Code is pushed to `main` branch under `data/`
- Manually triggered via GitHub Actions UI

Workflow file:

- `.github/workflows/deploy-existing-lambdas.yml`

### 4. Deployment Process

For each Lambda function:
1. Build a Docker image
2. Push the image to ECR (`:latest` tag)
3. Update the Lambda function code using the image URI (`aws lambda update-function-code --image-uri ...`)
4. Wait for update to complete

### 5. Manual Deployment (Local)

If you need to deploy manually (without GitHub Actions):

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin "$(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com"

# Build and push sync_and_fetch (repo root context)
docker build -t rearc-sync-and-fetch:latest -f data/lambda/sync_and_fetch/Dockerfile .
SYNC_URI=$(aws ecr describe-repositories --repository-names rearc-sync-and-fetch --query 'repositories[0].repositoryUri' --output text)
docker tag rearc-sync-and-fetch:latest "${SYNC_URI}:latest"
docker push "${SYNC_URI}:latest"

aws lambda update-function-code \
  --function-name rearc-sync-and-fetch \
  --image-uri "${SYNC_URI}:latest"
aws lambda wait function-updated --function-name rearc-sync-and-fetch

# Build and push analytics
docker build -t rearc-analytics:latest -f data/lambda/part3/Dockerfile data/lambda/part3
ANALYTICS_URI=$(aws ecr describe-repositories --repository-names rearc-analytics --query 'repositories[0].repositoryUri' --output text)
docker tag rearc-analytics:latest "${ANALYTICS_URI}:latest"
docker push "${ANALYTICS_URI}:latest"

aws lambda update-function-code \
  --function-name rearc-analytics \
  --image-uri "${ANALYTICS_URI}:latest"
aws lambda wait function-updated --function-name rearc-analytics
```

### 6. Testing Lambda Changes

After deployment, test locally:
```bash
aws lambda invoke \
  --function-name rearc-sync-and-fetch \
  --payload '{}' \
  response.json
cat response.json
```

## Infrastructure vs. Code Deployment

- **Infrastructure changes** (Terraform): Run `terraform apply` locally or via separate infrastructure pipeline
- **Code changes** (Lambda functions): Automatically deployed via GitHub Actions
- **Dependencies changes** (`requirements.txt`): Automatically included in deployment

## Rollback

To rollback to a previous version:
```bash
# List versions
aws lambda list-versions-by-function --function-name rearc-sync-and-fetch

# Rollback
aws lambda update-function-code \
  --function-name rearc-sync-and-fetch \
  --s3-bucket <previous-bucket> \
  --s3-key <previous-key>
```

Or redeploy from a previous Git commit.
