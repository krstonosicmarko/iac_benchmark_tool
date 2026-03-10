provider "aws" {
  region = "eu-central-1"
}

# SCALING CONTROL: Change this number for different scenarios
variable "resource_count" {
  description = "Number of complex S3 buckets to create"
  type        = number
  default     = 1  # Change to 10 for scaling scenario
}

# Generate random suffix for unique bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 buckets with simple complexity features
resource "aws_s3_bucket" "complex_buckets" {
  count  = var.resource_count
  bucket = "test-complex-bucket-mk-${count.index}-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "test-complex-bucket-${count.index}"
    Environment = "test"
    Purpose     = "benchmarking"
    Index       = count.index
  }
}

# Enable versioning for all buckets
resource "aws_s3_bucket_versioning" "complex_bucket_versioning" {
  count  = var.resource_count
  bucket = aws_s3_bucket.complex_buckets[count.index].id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption for all buckets
resource "aws_s3_bucket_server_side_encryption_configuration" "complex_bucket_encryption" {
  count  = var.resource_count
  bucket = aws_s3_bucket.complex_buckets[count.index].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Outputs for validation - handles multiple buckets
output "bucket_names" {
  value       = aws_s3_bucket.complex_buckets[*].id
  description = "Names of the created S3 buckets"
}

output "bucket_count" {
  value       = length(aws_s3_bucket.complex_buckets)
  description = "Number of complex buckets created"
}

output "bucket_region" {
  value       = aws_s3_bucket.complex_buckets[0].region
  description = "Region where buckets are created"
}

output "features_enabled" {
  value = {
    versioning = "Enabled"
    encryption = "AES256"
  }
  description = "Complex features enabled on all buckets"
}