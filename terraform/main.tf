provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "this" {
  bucket        = var.bucket_name
  force_destroy = var.force_destroy

  tags = var.tags
}

resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = var.versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.sse_algorithm
      kms_master_key_id = var.sse_algorithm == "aws:kms" ? var.kms_key_arn : null
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    id     = "transition-to-ia-and-glacier-ir"
    status = "Enabled"

    transition {
      days          = var.lifecycle_transition_to_standard_ia_days
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = var.lifecycle_transition_to_glacier_ir_days
      storage_class = "GLACIER_IR"
    }
  }
}

resource "aws_s3_bucket_intelligent_tiering_configuration" "this" {
  count  = var.enable_intelligent_tiering ? 1 : 0
  bucket = aws_s3_bucket.this.id
  name   = "entire-bucket"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = var.intelligent_tiering_archive_access_days
  }

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = var.intelligent_tiering_deep_archive_access_days
  }
}

locals {
  kms_key_required = var.sse_algorithm == "aws:kms"
}

resource "terraform_data" "validate_kms" {
  input = {
    kms_key_required = local.kms_key_required
    kms_key_arn      = var.kms_key_arn
  }

  lifecycle {
    precondition {
      condition     = !local.kms_key_required || try(trimspace(var.kms_key_arn), "") != ""
      error_message = "kms_key_arn must be set when sse_algorithm is aws:kms"
    }
  }
}
