# Outputs for Lambda and Queue

output "lambda_sync_and_fetch_arn" {
  description = "ARN of sync_and_fetch Lambda function"
  value       = aws_lambda_function.sync_and_fetch.arn
}

output "lambda_analytics_arn" {
  description = "ARN of analytics Lambda function"
  value       = aws_lambda_function.analytics.arn
}

output "sqs_queue_url" {
  description = "URL of the SQS queue"
  value       = aws_sqs_queue.data_pipeline.url
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge daily schedule rule"
  value       = aws_cloudwatch_event_rule.daily_sync.name
}
