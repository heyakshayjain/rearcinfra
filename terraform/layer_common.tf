resource "aws_lambda_layer_version" "common_code" {
  filename            = data.archive_file.common_layer.output_path
  layer_name          = "rearc-common-code"
  description         = "Shared code for Rearc data pipeline"
  source_code_hash    = data.archive_file.common_layer.output_base64sha256
  compatible_runtimes = ["python3.11"]
}

data "archive_file" "common_layer" {
  type        = "zip"
  output_path = "${path.module}/.terraform/layer_common.zip"
  source_dir  = "${path.module}/../data/lambda/common"
}
