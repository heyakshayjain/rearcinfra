# IAM Roles and Policies for Lambda Functions

# ===== Lambda 1: sync_and_fetch =====

resource "aws_iam_role" "lambda_sync_and_fetch" {
  name = "rearc-lambda-sync-and-fetch"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_policy" "lambda_sync_and_fetch" {
  name        = "rearc-lambda-sync-and-fetch-policy"
  description = "Permissions for sync_and_fetch Lambda: S3 write, CloudWatch logs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.this.arn,
          "${aws_s3_bucket.this.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:*:log-group:/aws/lambda/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_sync_and_fetch" {
  role       = aws_iam_role.lambda_sync_and_fetch.name
  policy_arn = aws_iam_policy.lambda_sync_and_fetch.arn
}


# ===== Lambda 2: analytics =====

resource "aws_iam_role" "lambda_analytics" {
  name = "rearc-lambda-analytics"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_policy" "lambda_analytics" {
  name        = "rearc-lambda-analytics-policy"
  description = "Permissions for analytics Lambda: S3 read, SQS, CloudWatch logs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.this.arn,
          "${aws_s3_bucket.this.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.data_pipeline.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:*:log-group:/aws/lambda/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_analytics" {
  role       = aws_iam_role.lambda_analytics.name
  policy_arn = aws_iam_policy.lambda_analytics.arn
}
