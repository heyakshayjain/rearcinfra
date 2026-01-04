# Rearc Data Quest - Data Pipeline

This repository contains a complete data pipeline solution for the Rearc Data Quest challenge.

## Repository Structure

```
rearcinfra/
├── terraform/              # Infrastructure as Code
│   ├── main.tf            # S3 bucket configuration
│   ├── lambda.tf          # Lambda functions (Part 4)
│   ├── sqs.tf             # SQS queue (Part 4)
│   └── ...
├── data/                   # Data processing code
│   ├── lambda/
│   │   ├── sync_and_fetch/ # Part 1 + Part 2 (Lambda container)
│   │   └── part3/          # Part 3 analytics (Lambda container)
│   └── notebooks/
│       └── part3_analytics.ipynb
├── README.md
└── rearc_todo.md          # Challenge requirements
```

## Quick Start

### Prerequisites
- AWS CLI configured with credentials
- Terraform >= 1.5.0
- Python 3.11+

### Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Build & Push Lambda Container Images

Terraform creates the ECR repositories. After `terraform apply`, build and push both images:

```bash
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin "$(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com"

# sync_and_fetch
docker build -t rearc-sync-and-fetch:latest -f data/lambda/sync_and_fetch/Dockerfile data/lambda/sync_and_fetch
docker tag rearc-sync-and-fetch:latest "$(cd terraform && terraform output -raw ecr_sync_and_fetch_url):latest"
docker push "$(cd terraform && terraform output -raw ecr_sync_and_fetch_url):latest"

# analytics
docker build -t rearc-analytics:latest -f data/lambda/part3/Dockerfile data/lambda/part3
docker tag rearc-analytics:latest "$(cd terraform && terraform output -raw ecr_analytics_url):latest"
docker push "$(cd terraform && terraform output -raw ecr_analytics_url):latest"

# update Lambdas to use the new images
cd terraform
terraform apply
```

### Local Testing (Optional)

```bash
cd data/lambda/part1
pip install -r requirements.txt
python -c "from handler import lambda_handler; lambda_handler({}, None)"
```

## Data Pipeline Architecture

The pipeline consists of 4 parts:

### Part 1: BLS Data Sync
- **What:** Syncs BLS time-series data from https://download.bls.gov/pub/time.series/pr/
- **Where:** `data/lambda/part1/handler.py`
- **Storage:** `s3://akshays3-2026/raw/bls/`
- **Schedule:** Daily via EventBridge

### Part 2: DataUSA Population API
- **What:** Fetches US population data from DataUSA API
- **Where:** `data/lambda/part2/handler.py`
- **Storage:** `s3://akshays3-2026/raw/datausa/population.json`
- **Schedule:** Daily via EventBridge

### Part 3: Data Analytics
- **What:** Analyzes BLS + population data (3 queries)
- **Where:** 
  - Lambda: `data/lambda/part3/handler.py`
  - Notebook: `data/notebooks/part3_analytics.ipynb`
- **Trigger:** SQS message when population.json is uploaded

### Part 4: Infrastructure Automation
- **What:** Terraform IaC orchestrating Lambda + EventBridge + SQS
- **Where:** `terraform/`

## Analytics Queries

1. **Population Statistics:** Mean & std-dev of US population (2013-2018)
2. **Best Year per Series:** Year with max quarterly sum for each series_id
3. **Series Join:** Match series PRS30006032 (Q01) with population by year

See `data/notebooks/part3_analytics.ipynb` for detailed analysis.

## S3 Bucket Configuration

- **Name:** `akshays3-2026`
- **Region:** `us-east-1`
- **Features:**
  - Versioning enabled
  - Server-side encryption (AES256)
  - Public access blocked
  - Intelligent-Tiering (Archive at 90d, Deep Archive at 180d)
  - Lifecycle: STANDARD_IA at 30d, GLACIER_IR at 60d

## Resources Created

- S3 bucket with lifecycle policies
- 3 Lambda functions (Part 1, 2, 3)
- EventBridge rule (daily schedule)
- SQS queue
- IAM roles and policies
- CloudWatch logs

## Testing

Run the notebook locally:
```bash
cd data/notebooks
jupyter notebook part3_analytics.ipynb
```

## Deploy `data/ingestion` to Lambda via GitHub Actions

This repo includes a zip-based Lambda deployment workflow for the ingestion code in `data/ingestion/`.

### One-time: Create the Lambda function

- Runtime: Python 3.11
- Handler: `data.ingestion.lambda_handler.handler`
- Ensure the Lambda execution role has permission to write to your S3 bucket.

### Configure GitHub Secrets

Add these GitHub Actions secrets:

- `AWS_REGION` (example: `us-east-1`)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `INGESTION_LAMBDA_FUNCTION_NAME` (example: `rearc-ingestion`)

Optional:

- `INGESTION_LAMBDA_SMOKE_INVOKE`: set to `true` to invoke the function after deploy.

### Deploy

- Push to `main` with changes under `data/ingestion/` or `data/constants.py`, or run the workflow manually.
- Workflow file: `.github/workflows/deploy-ingestion-lambda.yml`

## License

MIT
