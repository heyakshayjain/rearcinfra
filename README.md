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

### Deploy Code (Container Images)

This repo deploys the two Lambdas as **container images** using GitHub Actions.

- Workflow: `.github/workflows/deploy-existing-lambdas.yml`
- Trigger: push to `main` with changes under `data/` (or run manually)
- Required GitHub secrets: `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

### Local Testing (Optional)

```bash
# Build images locally
docker build -t rearc-sync-and-fetch:local -f data/lambda/sync_and_fetch/Dockerfile .
docker build -t rearc-analytics:local -f data/lambda/part3/Dockerfile data/lambda/part3

# Smoke test import (does not run the network/S3 sync)
docker run --rm --entrypoint python rearc-sync-and-fetch:local -c "import handler; print(handler.lambda_handler)"
```

## System Design

### Components

- **AWS S3**: stores republished BLS files (`raw/bls/`) and the DataUSA JSON (`raw/datausa/population.json`).
- **AWS Lambda (Image)**:
  - `rearc-sync-and-fetch`: runs Part 1 + Part 2 daily.
  - `rearc-analytics`: runs Part 3 when SQS receives a message.
- **Amazon EventBridge**: daily schedule triggers `rearc-sync-and-fetch`.
- **Amazon SQS**: receives a message when `population.json` is written to S3.
- **Amazon ECR**: stores the Docker images for both Lambdas.
- **GitHub Actions**: builds/pushes images and updates Lambda code to new image URIs.

### Architecture Diagram

```mermaid
flowchart LR
  EB[EventBridge schedule\n(daily)] --> L1[Lambda: rearc-sync-and-fetch\n(container image)]
  L1 -->|BLS files| S3[(S3 bucket\nraw/bls/*)]
  L1 -->|writes population.json| S3
  S3 -->|S3 notification\n(ObjectCreated: population.json)| SQS[SQS queue]
  SQS --> L2[Lambda: rearc-analytics\n(container image)]
  L2 --> CW[(CloudWatch Logs\nreports output)]

  subgraph CI[CI/CD]
    GH[GitHub Actions] --> ECR[(ECR repos\n:latest images)]
    ECR --> L1
    ECR --> L2
  end
```

## Code Logic (What Each Lambda Does)

### `rearc-sync-and-fetch` (Part 1 + Part 2)

- **Entry point:** `data/lambda/sync_and_fetch/handler.py`
- **Delegates to:** `data/ingestion/lambda_handler.py`
- **Runs:**
  - `data/ingestion/ingest.py`
    - Lists BLS directory contents (no hardcoded filenames)
    - Uploads *only changed/new* files to S3 (skips when size + stored BLS timestamp match)
    - Deletes S3 objects that no longer exist upstream (true sync)
  - `data/ingestion/usapi.py`
    - Fetches the DataUSA population API
    - Writes `raw/datausa/population.json` to S3

**Config:** `S3_BUCKET` is provided to the Lambda as an environment variable by Terraform. Defaults in `data/constants.py` still work for local runs.

### `rearc-analytics` (Part 3)

- **Entry point:** `data/lambda/part3/handler.py`
- **Trigger:** SQS messages created by the S3 notification when `population.json` is written
- **Logic:** loads BLS `pr.data.0.Current` and DataUSA JSON from S3 and logs the 3 reports required by the assignment.

## Analytics Queries

1. **Population Statistics:** Mean & std-dev of US population (2013-2018)
2. **Best Year per Series:** Year with max quarterly sum for each series_id
3. **Series Join:** Match series PRS30006032 (Q01) with population by year

See `data/notebooks/part3_analytics.ipynb` for detailed analysis.

## License

MIT
