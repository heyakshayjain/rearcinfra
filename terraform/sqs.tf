# SQS Queue and S3 Event Notification

# ===== SQS Queue =====

resource "aws_sqs_queue" "data_pipeline" {
  name                       = "rearc-data-pipeline-queue"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 86400
  receive_wait_time_seconds  = 20

  tags = var.tags
}

resource "aws_sqs_queue_policy" "data_pipeline" {
  queue_url = aws_sqs_queue.data_pipeline.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "s3.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.data_pipeline.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_s3_bucket.this.arn
        }
      }
    }]
  })
}


# ===== S3 Event Notification =====

resource "aws_s3_bucket_notification" "population_json_uploaded" {
  bucket = aws_s3_bucket.this.id

  queue {
    queue_arn     = aws_sqs_queue.data_pipeline.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "raw/datausa/"
    filter_suffix = ".json"
  }

  depends_on = [aws_sqs_queue_policy.data_pipeline]
}
