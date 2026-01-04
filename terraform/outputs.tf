output "bucket_name" {
  description = "S3 bucket name."
  value       = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  description = "S3 bucket ARN."
  value       = aws_s3_bucket.this.arn
}

output "bucket_id" {
  description = "S3 bucket ID (same as name)."
  value       = aws_s3_bucket.this.id
}

output "ecr_sync_and_fetch_url" {
  description = "ECR repository URL for the sync_and_fetch Lambda image."
  value       = aws_ecr_repository.sync_and_fetch.repository_url
}

output "ecr_analytics_url" {
  description = "ECR repository URL for the analytics Lambda image."
  value       = aws_ecr_repository.analytics.repository_url
}
