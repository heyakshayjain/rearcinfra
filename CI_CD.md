# CI/CD Setup for Lambda Deployment

## Overview

This repo uses GitHub Actions to automatically deploy Lambda function code changes to AWS.

## Setup

### 1. Configure AWS Credentials in GitHub Secrets

Go to your GitHub repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key

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
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction",
        "lambda:PublishVersion"
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
- Code is pushed to `main` branch in `data/lambda/` directory
- Manually triggered via GitHub Actions UI

### 4. Deployment Process

For each Lambda function:
1. Install uv (fast Python package installer)
2. Create virtual environment with uv
3. Install Python dependencies via uv
4. Package code + dependencies from venv into ZIP
5. Upload to Lambda via `aws lambda update-function-code`
6. Wait for update to complete
7. Verify deployment

### 5. Manual Deployment (Local)

If you need to deploy manually:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Deploy sync_and_fetch
cd data/lambda/sync_and_fetch
uv venv
uv pip install -r requirements.txt
cd .venv/lib/python3.11/site-packages
zip -r ../../../../deployment.zip .
cd ../../../../
zip -g deployment.zip handler.py
aws lambda update-function-code \
  --function-name rearc-sync-and-fetch \
  --zip-file fileb://deployment.zip

# Deploy analytics
cd data/lambda/part3
uv venv
uv pip install -r requirements.txt
cd .venv/lib/python3.11/site-packages
zip -r ../../../../deployment.zip .
cd ../../../../
zip -g deployment.zip handler.py
aws lambda update-function-code \
  --function-name rearc-analytics \
  --zip-file fileb://deployment.zip
```

### 6. Testing Lambda Changes

After deployment, test locally:
```bash
aws lambda invoke \
  --function-name rearc-sync-and-fetch \
  --payload '{"task": "part2"}' \
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
