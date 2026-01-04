variable "region" {
  description = "AWS region to deploy into (e.g., us-east-1)."
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Globally-unique S3 bucket name."
  type        = string
}

variable "force_destroy" {
  description = "If true, deletes all objects when destroying the bucket (dangerous in production)."
  type        = bool
  default     = false
}

variable "versioning" {
  description = "Enable S3 bucket versioning."
  type        = bool
  default     = true
}

variable "sse_algorithm" {
  description = "Server-side encryption algorithm: AES256 or aws:kms."
  type        = string
  default     = "AES256"

  validation {
    condition     = contains(["AES256", "aws:kms"], var.sse_algorithm)
    error_message = "sse_algorithm must be one of: AES256, aws:kms"
  }
}

variable "kms_key_arn" {
  description = "KMS key ARN to use when sse_algorithm is aws:kms."
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to resources."
  type        = map(string)
  default     = {}
}

variable "image_tag" {
  description = "Docker image tag to deploy for the Lambda container images."
  type        = string
  default     = "latest"
}

variable "enable_intelligent_tiering" {
  description = "Enable S3 Intelligent-Tiering for the bucket."
  type        = bool
  default     = true
}

variable "intelligent_tiering_archive_access_days" {
  description = "Days before transitioning objects to ARCHIVE_ACCESS tier (optional)."
  type        = number
  default     = 90
}

variable "intelligent_tiering_deep_archive_access_days" {
  description = "Days before transitioning objects to DEEP_ARCHIVE_ACCESS tier (optional)."
  type        = number
  default     = 180
}

variable "lifecycle_transition_to_standard_ia_days" {
  description = "Days before transitioning objects to STANDARD_IA via lifecycle (minimum 30)."
  type        = number
  default     = 30
}

variable "lifecycle_transition_to_glacier_ir_days" {
  description = "Days before transitioning objects to GLACIER_IR via lifecycle (must be >= lifecycle_transition_to_standard_ia_days)."
  type        = number
  default     = 60
}
