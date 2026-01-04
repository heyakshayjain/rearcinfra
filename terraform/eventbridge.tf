# EventBridge (CloudWatch Events) - Schedule sync_and_fetch Lambda

resource "aws_cloudwatch_event_rule" "daily_sync" {
  name                = "rearc-daily-sync"
  description         = "Trigger sync_and_fetch Lambda daily at 00:00 UTC"
  schedule_expression = "cron(0 0 * * ? *)"

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "lambda_sync_and_fetch" {
  rule      = aws_cloudwatch_event_rule.daily_sync.name
  target_id = "SyncAndFetchLambda"
  arn       = aws_lambda_function.sync_and_fetch.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sync_and_fetch.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_sync.arn
}
