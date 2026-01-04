# Lambda Functions

# ===== Lambda 1: sync_and_fetch (Part 1 + Part 2) =====

resource "aws_lambda_function" "sync_and_fetch" {
  function_name    = "rearc-sync-and-fetch"
  role             = aws_iam_role.lambda_sync_and_fetch.arn
  package_type     = "Image"
  image_uri        = "${aws_ecr_repository.sync_and_fetch.repository_url}:${var.image_tag}"
  timeout          = 300
  memory_size      = 512

  environment {
    variables = {
      S3_BUCKET = aws_s3_bucket.this.id
    }
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "lambda_sync_and_fetch" {
  name              = "/aws/lambda/${aws_lambda_function.sync_and_fetch.function_name}"
  retention_in_days = 7

  tags = var.tags
}


# ===== Lambda 2: analytics (Part 3) =====

resource "aws_lambda_function" "analytics" {
  function_name    = "rearc-analytics"
  role             = aws_iam_role.lambda_analytics.arn
  package_type     = "Image"
  image_uri        = "${aws_ecr_repository.analytics.repository_url}:${var.image_tag}"
  timeout          = 300
  memory_size      = 1024

  environment {
    variables = {
      S3_BUCKET = aws_s3_bucket.this.id
    }
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "lambda_analytics" {
  name              = "/aws/lambda/${aws_lambda_function.analytics.function_name}"
  retention_in_days = 7

  tags = var.tags
}

# SQS event source mapping for analytics Lambda
resource "aws_lambda_event_source_mapping" "analytics_sqs" {
  event_source_arn = aws_sqs_queue.data_pipeline.arn
  function_name    = aws_lambda_function.analytics.arn
  batch_size       = 1
  enabled          = true
}
