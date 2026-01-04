resource "aws_lambda_layer_version" "sync_and_fetch_deps" {
  filename            = "${path.module}/../data/lambda/sync_and_fetch/layer.zip"
  layer_name          = "rearc-sync-and-fetch-deps"
  source_code_hash    = filebase64sha256("${path.module}/../data/lambda/sync_and_fetch/layer.zip")
  compatible_runtimes = ["python3.11"]
}

resource "aws_lambda_layer_version" "analytics_deps" {
  filename            = "${path.module}/../data/lambda/part3/layer.zip"
  layer_name          = "rearc-analytics-deps"
  source_code_hash    = filebase64sha256("${path.module}/../data/lambda/part3/layer.zip")
  compatible_runtimes = ["python3.11"]
}
